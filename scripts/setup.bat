@echo off
echo Setting up Yeast Detection environment...

:: Create conda environment
echo Creating conda environment: yeast_detection
call conda create -n yeast_detection python=3.12 -y
call conda activate yeast_detection

:: Install PyTorch with CUDA
echo Installing PyTorch with CUDA support...
call conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia -y

:: Install other requirements
echo Installing other dependencies...
call pip install numpy opencv-python PyYAML matplotlib pillow ultralytics

:: Verify installation
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo Installation complete!