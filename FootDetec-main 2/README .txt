Project Overview
This project aims to optimize the convolutional layers of a pre-trained VGG16 model for shoe size detection by implementing a custom tiled matrix multiplication and kn2row convolution algorithm. The focus is on reducing inference time while maintaining accuracy, leveraging the AI3 framework for seamless integration.
________________


Features
1. Tiled Matrix Multiplication:
   * Custom implementation with variable tile sizes (4x4, 8x8, 16x16).
   * Optimized for memory locality and computational efficiency.
2. kn2row Convolution Algorithm:
   * Replaces memory-intensive im2col transformation.
   * Efficiently extracts patches and performs matrix multiplications.
3. Integration with AI3 Framework:
   * Replaces standard PyTorch Conv2D layers with optimized kn2row operations.
   * Allows dynamic layer selection for enhanced performance.
4. Foot Detection and Shoe Size Mapping:
   * Uses OpenCV for detecting foot dimensions.
   * Maps detected foot length to a shoe size using a predefined size chart.
5. Performance Benchmarking:
   * Compares inference time between the standard PyTorch model and the AI3-enhanced model.
   * Experiments with different tile sizes to evaluate performance improvements.
________________


Setup Instructions
Prerequisites
* Python 3.11
* PyTorch
* AI3 Framework (developed by TA Timothy)
* OpenCV
* PIL (Pillow)
Installation
1. Clone the repository:


git clone https://github.com/your-repo-url/ai3-project.git
cd ai3-project

2. Install required dependencies:


pip install -r requirements.txt

3. Install AI3 Framework:


module load Python/3.11.5-GCCcore-13.2.0
module use /path/to/custom/modulefiles
module load SYCL/2024.0.1.46
pip install torch>=2.4
cd ai3
pip install .

4. Verify installation:


import ai3
print("SYCL available:", ai3.using_sycl())
Usage
1. Run the Model
To execute the model for shoe size detection and benchmarking:


python MainProgram.py

2. Input Requirements
* Provide an image of a foot in .jpg or .png format.
* Ensure the image is clear and contains only the foot.
3. Outputs
* Bounding box of the detected foot.
* Predicted shoe size based on foot length.
* Inference time for both standard and optimized models.
4. Performance Comparison
Run the benchmark.py script to compare the execution time of the standard PyTorch model and the AI3-enhanced model with different tile sizes:


python benchmark.py

File Structure


ai3-project/
├── main.py          # Main script for model execution
├── kn2row.py        # kn2row convolution algorithm
├── tiled_matrix.py  # Tiled matrix multiplication implementation
├── benchmark.py     # Performance benchmarking script
├── requirements.txt # Dependencies list
├── sample_image.jpg # Example input image
└── detected_foot.jpg # Output image with bounding box



Results




Tile Size
	Standard PyTorch Time (s)
	kn2row Optimized Time (s)
	Improvement (%)
	4x4
	0.85
	0.68
	20.0%
	8x8
	0.85
	0.62
	27.1%
	16x16
	0.85
	0.59
	30.6%
	



Future Work
* Extend the implementation to support additional layers (e.g., fully connected layers).
* Optimize memory allocation strategies for larger tile sizes.
* Evaluate the performance on different hardware platforms such as GPUs and TPUs.
* Improve Foot Detection Algorithm
* Automated Hyperparameter Optimization:
Acknowledgements :  We thank Professor Sanmukh Kuppannagari and TA Timothy  for providing the AI3 framework and guidance throughout the project.