# SPDX-License-Identifier: Apache-2.0

from . import _core, layers, errors, utils
from typing import Mapping, Optional, List, Sequence, Union, DefaultDict, Tuple, Type
from collections import defaultdict
import torch
from torch import nn, fx, ops, relu  # type: ignore
from torch.nn import grad
from torch.fx import passes
from packaging import version

MIN_TORCH_VERSION = '2.4'

errors.bail_if(version.parse(torch.__version__) < version.parse(
    MIN_TORCH_VERSION), 'requires torch >= 2.4')


class Conv2D(nn.Module):
    def __init__(self, orig: nn.Conv2d, algorithm: str):
        super(Conv2D, self).__init__()
        self.algorithm = algorithm

        self.stride = utils.make_2d(orig.stride)
        self.dilation = utils.make_2d(
            orig.dilation)
        self.padding = utils.make_padding_2d(
            orig.padding, self.stride, self.dilation, orig.weight.size())
        errors.bail_if(
            orig.padding_mode
            not in ['zeros', 'reflect', 'replicate', 'circular'],
            f'invalid padding mode: {orig.padding_mode}')
        self.groups = orig.groups
        self.padding_mode = {
            'zeros': _core.PaddingMode.zeros,
            'reflect': _core.PaddingMode.reflect,
            'replicate': _core.PaddingMode.replicate,
            'circular': _core.PaddingMode.circular
        }[orig.padding_mode]
        self.weight = orig.weight
        self.bias = orig.bias
        if self.bias is not None:
            self.bias_data_ptr = self.bias.data_ptr()
        else:
            self.bias_data_ptr = None

    def forward(self, x: torch.Tensor):
        assert (callable(ops.ai3.conv2d))
        return ops.ai3.conv2d(
            x, self.weight, self.bias, self.padding[0],
            self.padding[1],
            self.stride[0],
            self.stride[1],
            self.dilation[0],
            self.dilation[1],
            int(self.padding_mode),
            self.groups, self.algorithm)


op_str_to_type: Mapping[str, Union[Type, List[Type]]] = {
    'conv2d': [nn.Conv2d, Conv2D],
    'linear': nn.Linear,
    'maxpool2d': nn.MaxPool2d,
    'avgpool2d': nn.AvgPool2d,
    'adaptiveavgpool2d': nn.AdaptiveAvgPool2d,
    'relu': nn.ReLU,
    'flatten': nn.Flatten
}


def str_to_op_type(op_type_str: str) -> Type:
    if op_type_str in op_str_to_type:
        op_type = op_str_to_type[op_type_str]
        if isinstance(op_type, list):
            return op_type[0]
        return op_type
    else:
        errors.unsupported_mod(op_type_str)


def op_type_to_str(op_type: Type) -> str:
    for op_str, op_types in op_str_to_type.items():
        if isinstance(op_types, list):
            if op_type in op_types:
                return op_str
        elif op_type == op_types:
            return op_str
    errors.unsupported_mod(op_type)


def iscontainer(name: str) -> bool:
    return '.' in name


def getmodule(module: nn.Module, name) -> nn.Module:
    if iscontainer(name):
        names = name.split('.', 1)
        return getmodule(getattr(module, names[0]), names[1])
    else:
        return getattr(module, name)


def setmodule(module: nn.Module, name, new: nn. Module) -> nn.Module:
    if iscontainer(name):
        names = name.split('.', 1)
        setmodule(
            getattr(module, names[0]), names[1], new)
    else:
        setattr(module, name, new)
    return module


def conv2d(input: torch.Tensor,
           weight: torch.Tensor, bias: Optional[torch.Tensor],
           padding_h: int, padding_w: int, stride_h: int, stride_w: int,
           dilation_h: int, dilation_w: int, padding_mode: int, groups: int,
           algorithm: str) -> torch.Tensor:
    if bias is not None:
        bias_ptr = bias.data_ptr()
    else:
        bias_ptr = None

    requires_grad = False
    if input.requires_grad or weight.requires_grad or (
            bias is not None and bias.requires_grad):
        requires_grad = True
    out = _core.conv2d(
        input.data_ptr(), input.shape, utils.get_scalar_type(input.dtype),
        weight.data_ptr(), weight.shape, bias_ptr, padding_h, padding_w,
        stride_h, stride_w, dilation_h, dilation_w, padding_mode, groups,
        algorithm)
    buffer = torch.frombuffer(
        out, dtype=input.dtype, requires_grad=requires_grad).view(
        out.shape)
    return buffer.clone() if requires_grad else buffer


def conv2d_abstract(
        input: torch.Tensor, weight: torch.Tensor, bias: torch.Tensor,
        padding_h: int, padding_w: int, stride_h: int, stride_w: int,
        dilation_h: int, dilation_w: int, padding_mode: int, groups: int,
        algorithm: str) -> torch.Tensor:
    if len(input.shape) == 4:
        n = input.shape[0]
        _, h, w = input.shape[1:]
    else:
        n = None
        _, h, w = input.shape
    del bias, padding_mode, groups, algorithm
    out_c = weight.shape[0]
    height = _core.output_hw_for_2d(
        h, weight.shape[2], padding_h, dilation_h, stride_h)
    width = _core.output_hw_for_2d(
        w, weight.shape[3], padding_w, dilation_w, stride_w)
    if n:
        s = (n, out_c, height, width)
    else:
        s = (out_c, height, width)
    return torch.empty(s, dtype=input.dtype, device='cpu')


def conv2d_backward(ctx, out_grad):
    input, weight = ctx.saved_tensors
    padding_h, padding_w, stride_h, stride_w, dilation_h, dilation_w, padding_mode, groups = ctx.hparams
    del padding_mode

    grad_input = grad_weight = grad_bias = None

    if len(input.shape) == 3:
        input = input.reshape(1, *input.shape)
    if len(out_grad.shape) == 3:
        out_grad = out_grad.reshape(
            1, *out_grad.shape)

    if ctx.needs_input_grad[0]:
        grad_input = grad.conv2d_input(
            input.shape, weight, out_grad,
            stride=(stride_h, stride_w),  # type: ignore
            padding=(padding_h, padding_w),  # type: ignore
            dilation=(dilation_h, dilation_w),  # type: ignore
            groups=groups
        )

    if ctx.needs_input_grad[1]:
        grad_weight = grad.conv2d_weight(
            input, weight.shape, out_grad,
            stride=(stride_h, stride_w),  # type: ignore
            padding=(padding_h, padding_w),  # type: ignore
            dilation=(dilation_h, dilation_w),  # type: ignore
            groups=groups
        )

    if ctx.needs_input_grad[2]:
        if len(out_grad.shape) == 4:
            grad_bias = out_grad.sum(
                dim=(0, 2, 3))
        elif len(out_grad.shape) == 3:
            grad_bias = out_grad.sum(dim=(1, 2))
        else:
            errors.bail(
                f'conv2d output gradient must be 3 or 4 dimensions but is {len(out_grad.shape)} dimensions')

    return grad_input, grad_weight, grad_bias, None, None, None, None, None, None, None, None, None


def setup_context(ctx, inputs, output):
    (input, weight, bias, padding_h, padding_w, stride_h, stride_w,
     dilation_h, dilation_w, padding_mode, groups, algorithm) = inputs
    del output, algorithm, bias

    saved_input = saved_weight = None
    if ctx.needs_input_grad[0] or ctx.needs_input_grad[1] or ctx.needs_input_grad[2]:
        saved_input = input.clone()
        saved_weight = weight.clone()
    assert not hasattr(ctx, 'hparams')
    ctx.hparams = (padding_h, padding_w, stride_h, stride_w,
                   dilation_h, dilation_w, padding_mode, groups)
    ctx.save_for_backward(
        saved_input, saved_weight)


torch.library.custom_op(
    'ai3::conv2d', conv2d, mutates_args=())
torch.library.register_fake(
    'ai3::conv2d', conv2d_abstract)
torch.library.register_autograd(
    'ai3::conv2d', conv2d_backward, setup_context=setup_context)


def get_algo_inc_counter(orig: Union[nn.Module, str],
                         algo_selector: utils.AlgorithmicSelector,
                         layer_counters: DefaultDict[str, int],
                         input_shape: Optional[Sequence[int]],
                         *, swapping_backend=False) -> str:
    if isinstance(orig, nn.Module):
        op = op_type_to_str(type(orig))
    else:
        op = orig
    if callable(algo_selector):
        errors.bail_if(
            isinstance(orig, str),
            f'trying to use function selector for something that is not an instantiable')
        if input_shape is not None:
            algo = algo_selector(orig, input_shape)
        else:
            algo = algo_selector(orig)
    elif isinstance(algo_selector, list):
        algo = algo_selector[layer_counters[op]]
        layer_counters[op] += 1
    elif isinstance(algo_selector, str):
        algo = algo_selector
    else:
        errors.bail(f'unsupported selector: {type(algo_selector)}')
    errors.bail_if(swapping_backend and algo == 'torch',
                   f'cannot use {algo} implementation when swapping backend')
    errors.bail_if(not isinstance(algo, str),
                   f'invalid algorithm, {algo}, found for {op}')
    errors.bail_if(not algo in utils.SUPPORTED_ALGORITHMS[op],
                   f'algorithm, {algo}, is unsupported for {op}')
    return algo


def trace_module(module: nn.Module,
                 sample_input_shape: Optional[Sequence[int]] = None) -> Tuple[fx.Graph, bool]:
    tracer = Tracer()
    graph: fx.Graph = tracer.trace(module)
    with_shapes = False
    if sample_input_shape is not None:
        gm = fx.GraphModule(module, graph)
        passes.shape_prop.ShapeProp(gm).propagate(
            torch.randn(sample_input_shape))
        graph = gm.graph
        with_shapes = True
    return graph, with_shapes


def convert_layers(complete_module: nn.Module, dtype,
                   algos: Mapping[str, utils.AlgorithmicSelector],
                   sample_input_shape: Optional[Sequence[int]] = None) -> List[layers.Layer]:
    graph, with_shapes = trace_module(
        complete_module, sample_input_shape)

    forwards = []

    layer_counters = defaultdict(int)

    node_input_shape = None
    for node in graph.nodes:
        assert isinstance(node, fx.Node)
        if with_shapes:
            node_input_shape = node.meta['tensor_meta'].shape
        if node.op == 'placeholder' or node.op == 'output':
            continue
        elif node.op == 'call_function':
            if node.target == torch.flatten:
                start_dim = 0
                end_dim = -1
                if len(node.args) > 1:
                    start_dim = node.args[1]
                if len(node.args) > 2:
                    end_dim = node.args[2]
                if 'start_dim' in node.kwargs:
                    start_dim = node.kwargs['start_dim']
                if 'end_dim' in node.kwargs:
                    end_dim = node.kwargs['end_dim']
                algo = get_algo_inc_counter(
                    'flatten', algos['flatten'],
                    layer_counters, node_input_shape, swapping_backend=True)
                assert (isinstance(
                    start_dim, int))
                assert (isinstance(end_dim, int))
                layer = layers.Flatten(start_dim, end_dim, algo)
            elif node.target == torch.relu:
                algo = get_algo_inc_counter(
                    'relu', algos['relu'],
                    layer_counters, node_input_shape, swapping_backend=True)
                layer = layers.ReLU(algo)
            else:
                errors.unsupported_mod(node.target)
        elif node.op == 'call_module':
            mod = getmodule(
                complete_module, node.target)
            if isinstance(mod, nn.Dropout):
                continue
            algo = get_algo_inc_counter(mod, algos[op_type_to_str(type(mod))],
                                        layer_counters, node_input_shape,
                                        swapping_backend=True)
            layer = swap_layer(
                mod, dtype, algo)
        else:
            errors.bail(
                f'unsupported operation: {node.op}')
        forwards.append(layer)

    return forwards


class Tracer(fx.Tracer):
    def is_leaf_module(self, m, module_qualified_name):
        if isinstance(m, Conv2D):
            return True
        return super().is_leaf_module(m, module_qualified_name)


def default_dtype():
    return torch.get_default_dtype()


def swapped_type(op_type) -> Optional[Type]:
    if op_type == nn.Conv2d:
        return Conv2D
    return None


def swap_operation(
        orig_op_type: Type, module: nn.Module,
        selector: utils.AlgorithmicSelector,
        sample_input_shape: Optional[Sequence[int]],
        swap_with):
    if not swap_with:
        swap_with = swapped_type(orig_op_type)
    errors.bail_if(
        swap_with is None,
        f'cannot perform inplace algorithmic selection for {orig_op_type}')
    assert swap_with is not None
    graph, with_shapes = trace_module(
        module, sample_input_shape)

    layer_counters = defaultdict(int)
    node_input_shape = None
    for node in graph.nodes:
        assert isinstance(node, fx.Node)
        if with_shapes:
            node_input_shape = node.meta['tensor_meta'].shape
        if node.op == 'call_module':
            mod = getmodule(module, node.target)
            if isinstance(mod, (orig_op_type, swap_with)):
                algo = get_algo_inc_counter(
                    mod, selector,
                    layer_counters, node_input_shape)
                if algo == 'torch':
                    continue
                if isinstance(mod, orig_op_type):
                    module = setmodule(
                        module, node.target,
                        swap_with(mod, algo))
                else:
                    setattr(mod, 'algorithm', algo)


def swap_layer(module: Union[nn.Module, layers.Layer],
               dtype, algo: str) -> layers.Layer:
    scalar_type = utils.get_scalar_type(dtype)
    if isinstance(module, (nn.Conv2d, Conv2D)):
        return layers.Conv2D(
            module.weight, module.bias, module.stride, module.padding,
            module.dilation, module.padding_mode, module.groups, algo, scalar_type)
    elif isinstance(module, nn.Linear):
        return layers.Linear(module.weight, module.bias, algo, scalar_type)
    elif isinstance(module, nn.MaxPool2d):
        return layers.MaxPool2D(
            module.kernel_size, module.stride, module.padding, module.dilation,
            module.ceil_mode, algo)
    elif isinstance(module, nn.AvgPool2d):
        return layers.AvgPool2D(module.kernel_size, module.stride,
                                module.padding, module.ceil_mode,
                                module.count_include_pad,
                                module.divisor_override, algo)
    elif isinstance(module, nn.AdaptiveAvgPool2d):
        return layers.AdaptiveAvgPool2D(module.output_size, algo)
    elif isinstance(module, nn.ReLU):
        return layers.ReLU(algo)
    elif isinstance(module, nn.Flatten):
        return layers.Flatten(module.start_dim, module.end_dim, algo)
    errors.unsupported_mod(module)