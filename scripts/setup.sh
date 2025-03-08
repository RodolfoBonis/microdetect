#!/bin/bash

echo "Setting up Yeast Detection environment..."

# Function to detect platform
detect_platform() {
    if [[ "$(uname)" == "Darwin"* ]]; then
        # Check if M1/M2 Mac
        if [[ "$(uname -m)" == "arm64" ]]; then
            echo "mac_arm"
        else
            echo "mac_intel"
        fi
    elif [[ "$(grep -i microsoft /proc/version 2>/dev/null)" ]]; then
        echo "wsl"
    else
        echo "linux"
    fi
}

# Create and activate conda environment
create_env() {
    echo "Creating conda environment: yeast_detection"
    conda create -n yeast_detection python=3.12 -y

    # Source doesn't work in scripts, inform user to activate manually
    echo "Please activate the environment manually with:"
    echo "conda activate yeast_detection"
    echo "Then run this script again with the --install flag"
}

# Install platform-specific dependencies
install_deps() {
    platform=$(detect_platform)
    echo "Detected platform: $platform"

    # Install common dependencies
    echo "Installing common dependencies..."
    pip install numpy opencv-python PyYAML matplotlib pillow

    # Platform-specific installations
    if [[ "$platform" == "mac_arm" ]]; then
        echo "Installing PyTorch for Mac M1/M2..."
        pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu

        # Verify MPS is available
        python -c "import torch; print(f'PyTorch version: {torch.__version__}'); \
                  print(f'MPS available: {torch.backends.mps.is_available()}')"

    elif [[ "$platform" == "mac_intel" ]]; then
        echo "Installing PyTorch for Mac Intel..."
        conda install pytorch torchvision -c pytorch -y

    elif [[ "$platform" == "wsl" || "$platform" == "linux" ]]; then
        echo "Installing PyTorch with CUDA support for Linux/WSL..."
        conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y

        # Verify CUDA is available
        python -c "import torch; print(f'PyTorch version: {torch.__version__}'); \
                  print(f'CUDA available: {torch.cuda.is_available()}')"
    fi

    # Install optree Update for faster inference
    echo "Installing optree Update for faster inference..."
    pip install --upgrade 'optree>=0.13.0'

    # Install YOLOv8
    echo "Installing Ultralytics YOLOv8..."
    pip install ultralytics

    echo "Installation complete!"
}

# Main execution
if [[ "$1" == "--create" ]]; then
    create_env
elif [[ "$1" == "--install" ]]; then
    install_deps
else
    echo "Usage:"
    echo "  ./setup.sh --create   # Create conda environment"
    echo "  ./setup.sh --install  # Install dependencies (run after activating environment)"
fi