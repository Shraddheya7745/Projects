# Import necessary libraries
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image, UnidentifiedImageError
import cv2
import ai3
import time

# Step 1: Preprocess the Input Image
def preprocess_image(image_path):
    """Preprocess the input image for VGG16."""
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to 224x224
        transforms.ToTensor(),         # Convert to tensor
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],  # Normalize using ImageNet mean
            std=[0.229, 0.224, 0.225]    # Normalize using ImageNet std
        )
    ])
    try:
        image = Image.open(image_path).convert('RGB')
        print(f"Successfully loaded image: {image_path}")
        return transform(image).unsqueeze(0).cuda()  # Add batch dimension and move to GPU
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        raise
    except UnidentifiedImageError:
        print("Error: Unable to identify the image format. Please provide a valid image.")
        raise

# Step 2: Detect Foot Dimensions
def detect_foot(image_path):
    """Detect the foot region and return its bounding box."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            print("Error: Unable to load image using OpenCV.")
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Find contours of the foot
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            return x, y, w, h
        else:
            print("Error: No foot detected in the image.")
            return None
    except Exception as e:
        print(f"Error during foot detection: {e}")
        return None

# Step 3: Map Foot Length to Shoe Size
def map_to_shoe_size(length_cm):
    """Map foot length in cm to US shoe size."""
    size_chart = [
        (22.5, "US Size 5"),
        (23.0, "US Size 6"),
        (24.0, "US Size 7"),
        (25.0, "US Size 8"),
        (26.0, "US Size 9"),
        (27.0, "US Size 10"),
    ]
    for length, size in size_chart:
        if length_cm <= length:
            return size
    return "Size not found as image is not good"

# Step 4: Auto Selector for AI3
def auto_selector(orig: torch.nn.Conv2d, input_shape):
    """Layer selection for AI3."""
    if orig.out_channels < 64:
        return 'default'
    return 'default'

# Step 5: Load and Convert VGG16 Model with AI3
vgg16 = models.vgg16(weights=models.VGG16_Weights.DEFAULT).eval()
model = ai3.convert(vgg16, {'conv2d': auto_selector}, sample_input_shape=(1, 3, 224, 224))

# Step 6: Load and Preprocess the Image
image_path = "/home/axg1503/CSDS451/Project/ai3/sample_image.jpg"  # Replace with your image path
try:
    input_data = preprocess_image(image_path)
    print("Input shape:", input_data.shape)

    # Step 7: Detect Foot Dimensions
    bounding_box = detect_foot(image_path)
    if bounding_box:
        x, y, w, h = bounding_box
        print(f"Bounding box of foot: x={x}, y={y}, width={w}, height={h}")

        # Assuming a scale of 1 pixel = 0.1 cm (Adjust scale as per your setup)
        foot_length_cm = w * 0.1
        shoe_size = map_to_shoe_size(foot_length_cm)
        print(f"Predicted shoe size: {shoe_size}")

    # Step 8: Run Inference on the Converted Model
    start = time.time()
    output = model(input_data)
    end = time.time()

    print(f"Model output shape: {output.shape}")
    print(f"Inference time: {end - start:.4f} seconds")

    # Step 9: Interpret Model Output
    _, predicted_class = output.max(1)
    print(f"Predicted class: {predicted_class.item()}")

except Exception as e:
    print(f"Error: {e}")
