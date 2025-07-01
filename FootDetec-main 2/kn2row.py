from tiled_matrix import tiled_matrix_multiplication

class Kn2RowConvolution:
    def __call__(self, input_tensor, kernel, tile_size):
        """Perform convolution using the kn2row algorithm."""
        B, C, H, W = input_tensor.shape  # Batch, Channels, Height, Width
        out_channels, _, kernel_h, kernel_w = kernel.shape
        out_h = H - kernel_h + 1
        out_w = W - kernel_w + 1

        # Initialize output tensor
        output = torch.zeros(B, out_channels, out_h, out_w, device=input_tensor.device)

        # Perform convolution using tiled matrix multiplication
        for b in range(B):  # For each image in the batch
            for oc in range(out_channels):
                for i in range(out_h):
                    for j in range(out_w):
                        # Perform element-wise convolution
                        region = input_tensor[b, :, i:i+kernel_h, j:j+kernel_w]
                        output[b, oc, i, j] = torch.sum(region * kernel[oc])
        return output
