import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import ai3

# Load VGG16 model
vgg16 = models.vgg16(weights=models.VGG16_Weights.DEFAULT).eval()

# Define AI3 layer selector
def auto_selector(orig: torch.nn.Conv2d, input_shape):
    if orig.out_channels < 64:
        return 'default'  # Use default implementation for small layers
    return 'default'      # Replace with AI3-specific logic as needed


# Convert the model using AI3
model = ai3.convert(
    vgg16,
    {'conv2d': auto_selector},
    sample_input_shape=(1, 3, 224, 224)
)


# Preprocess the input image
def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize the image to 224x224
        transforms.ToTensor(),         # Convert to tensor
        transforms.Normalize(          # Normalize with ImageNet mean and std
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    image = Image.open(image_path).convert('RGB')
    return transform(image).unsqueeze(0).cuda()  # Add batch dimension and move to GPU

# Load and preprocess the image
image_path = "/home/axg1503/CSDS451/Project/ai3/sample_image.jpg"  # Replace with your image path
input_data = preprocess_image(image_path)
print("Input shape:", input_data.shape)

# Run inference on the converted model
output = model(input_data)
print("Model output shape:", output.shape)

# Interpret the output (e.g., map logits to class labels)
_, predicted_class = output.max(1)
print(f"Predicted class: {predicted_class.item()}")


