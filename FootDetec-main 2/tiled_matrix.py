import torch

def tiled_matrix_multiplication(A, B, tile_size):
    """Perform tiled matrix multiplication."""
    assert A.size(1) == B.size(0), "Incompatible matrix dimensions for multiplication"
    C = torch.zeros(A.size(0), B.size(1), device=A.device)  # Result matrix
    for i in range(0, A.size(0), tile_size):
        for j in range(0, B.size(1), tile_size):
            for k in range(0, A.size(1), tile_size):
                # Multiply tiles
                C[i:i+tile_size, j:j+tile_size] += torch.mm(
                    A[i:i+tile_size, k:k+tile_size],
                    B[k:k+tile_size, j:j+tile_size]
                )
    return C



A = torch.rand(64, 128, device='cuda')
B = torch.rand(128, 64, device='cuda')
tile_size = 32
C = tiled_matrix_multiplication(A, B, tile_size)
print(C)
