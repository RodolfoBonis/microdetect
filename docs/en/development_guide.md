# Development Guide

This guide provides information for developers who want to contribute to the MicroDetect project.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Setting Up Development Environment](#setting-up-development-environment)
- [Contribution Guidelines](#contribution-guidelines)
- [Development Workflow](#development-workflow)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Build and Release Process](#build-and-release-process)
- [Common Development Tasks](#common-development-tasks)
- [Troubleshooting Development Issues](#troubleshooting-development-issues)
- [Resources for Developers](#resources-for-developers)
- [Contact and Support](#contact-and-support)

## Architecture Overview

MicroDetect follows a modular architecture, organized into packages and functional modules:

```
microdetect/
├── __init__.py                 # Package initialization
├── cli.py                      # Command-line interface
├── data/                       # Data processing
│   ├── __init__.py
│   ├── augmentation.py         # Image augmentation
│   ├── conversion.py           # Format conversion
│   └── dataset.py              # Dataset management
├── annotation/                 # Annotation tools
│   ├── __init__.py
│   ├── annotator.py            # Annotation interface
│   └── visualization.py        # Annotation visualization
├── training/                   # Training modules
│   ├── __init__.py
│   ├── train.py                # Model trainer
│   └── evaluate.py             # Model evaluation
└── utils/                      # Utilities
    ├── __init__.py
    ├── config.py               # Configuration management
    ├── updater.py              # Update system
    └── aws_setup.py            # AWS configuration
```

### Control Flow

1. The main entry point is `cli.py`
2. Commands are dispatched to specific handlers
3. Each module is responsible for a specific functionality
4. The centralized configuration system manages parameters

## Setting Up Development Environment

### Installing Development Dependencies

```bash
# Clone the repository
git clone https://github.com/YourUsername/microdetect.git
cd microdetect

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install production and development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools

# Install the package in editable mode
pip install -e .

# Set up pre-commit hooks
pre-commit install
```

### Development Tools

The project uses the following development tools:

- **Black**: Code formatter
- **isort**: Import organizer
- **flake8**: Linter for code quality
- **pytest**: Testing framework
- **pytest-cov**: Code coverage measurement
- **pre-commit**: Git hooks for automatic checks
- **twine**: For package publishing
- **sphinx**: For documentation generation

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=microdetect

# Generate HTML coverage report
pytest --cov=microdetect --cov-report=html

# Run specific tests
pytest tests/test_specific_module.py

# Run tests with detailed output
pytest -v
```

### Checking Code Quality

```bash
# Check formatting with black
black --check microdetect

# Format code with black
black microdetect

# Check imports with isort
isort --check-only --profile black microdetect

# Organize imports
isort --profile black microdetect

# Check with flake8
flake8 microdetect

# Run all quality checks
pre-commit run --all-files
```

## Contribution Guidelines

### Git Workflow

1. **Forks and Branches**:
   - Fork the repository
   - Create a branch for your feature or fix:
     ```bash
     git checkout -b feature/your-feature-name
     # or
     git checkout -b fix/your-bug-name
     ```

2. **Commits**:
   - Use meaningful commit messages following [Conventional Commits](https://www.conventionalcommits.org/):
     ```
     feat: add support for processing multi-page TIFFs
     fix: correct annotation loading for non-standard paths
     docs: improve installation instructions
     test: add test cases for dataset splitting
     refactor: optimize augmentation pipeline
     ```

3. **Pull Requests**:
   - Make your changes and create a Pull Request to the `main` branch
   - Describe your changes in detail
   - Reference related issues using `#issue_number`
   - Wait for code review

### Code Style

- Follow the [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use Black with default configuration (max line length of 127 characters as configured)
- Use static typing with [type hints](https://docs.python.org/3/library/typing.html):
  ```python
  def process_image(image_path: str, output_dir: Optional[str] = None) -> bool:
      # implementation
  ```
- Use Google-style docstrings:
  ```python
  def function(arg1: int, arg2: str) -> bool:
      """
      Short description of function.
      
      Longer description explaining details.
      
      Args:
          arg1: Description of arg1
          arg2: Description of arg2
              
      Returns:
          Description of return value
              
      Raises:
          ValueError: Description of when this error is raised
      """
  ```

### Testing

- Write tests for all new features and fixes
- Maintain or improve existing test coverage
- Structure tests to mirror the source code structure:
  ```
  tests/
  ├── test_cli.py
  ├── data/
  │   ├── test_augmentation.py
  │   ├── test_conversion.py
  │   └── test_dataset.py
  ├── annotation/
  │   ├── test_annotator.py
  │   └── test_visualization.py
  ├── training/
  │   ├── test_train.py
  │   └── test_evaluate.py
  └── utils/
      ├── test_config.py
      ├── test_updater.py
      └── test_aws_setup.py
  ```

# Documentation

## Documentation Packaging and Access

The MicroDetect project now includes a comprehensive documentation system that is properly packaged with the distribution. This section explains how the documentation is structured, packaged, and served.

## Documentation Structure

The documentation is organized in a language-based structure:

```
docs/
├── en/                          # English documentation
│   ├── index.md                 # Main entry point
│   ├── installation_guide.md    # Installation instructions
│   ├── ...                      # Other topic files
└── pt/                          # Portuguese documentation
    ├── index.md                 # Main entry point (Portuguese)
    ├── installation_guide.md    # Installation instructions (Portuguese)
    └── ...                      # Other topic files
```

## Documentation Packaging

The documentation is included in the MicroDetect package during the build process using two mechanisms:

### 1. MANIFEST.in Configuration

The `MANIFEST.in` file includes the following directives to include documentation files:

```
recursive-include docs *.md
recursive-include docs *.html
recursive-include docs *.css
recursive-include docs *.js
recursive-include docs *.png
recursive-include docs *.jpg
recursive-include docs *.svg
```

### 2. setup.py Configuration

The `setup.py` file includes code to collect and organize documentation files:

```python
# Collect all documentation files
doc_files = glob.glob('docs/**/*.md', recursive=True)
doc_files += glob.glob('docs/**/*.html', recursive=True)
doc_files += glob.glob('docs/**/*.css', recursive=True)
# ...etc.

# Organize doc files by directory structure
doc_dirs = {}
for doc_file in doc_files:
    rel_dir = os.path.dirname(doc_file)
    if rel_dir not in doc_dirs:
        doc_dirs[rel_dir] = []
    doc_dirs[rel_dir].append(doc_file)

# Create data_files entries for each directory
doc_data_files = []
for rel_dir, files in doc_dirs.items():
    install_dir = os.path.join('share/microdetect', rel_dir)
    doc_data_files.append((install_dir, files))

# Add to setup
setup(
    # ...other setup parameters...
    data_files=doc_data_files,
)
```

This ensures that documentation files are properly installed in the `share/microdetect/docs/` directory of the Python package.

## Documentation Server

The MicroDetect CLI includes a built-in documentation server:

```python
# In microdetect/utils/docs_server.py
```

This module provides:

1. A web server that renders Markdown files as HTML
2. A navigation sidebar with organized documentation links
3. Language switching between English and Portuguese
4. Search functionality
5. The ability to run in background mode

## CLI Commands for Documentation

Two main commands have been implemented for documentation access:

### 1. `microdetect docs`

Starts the documentation server:

```bash
# Basic usage
microdetect docs

# Language options
microdetect docs --lang pt  # Portuguese
microdetect docs --lang en  # English (default)

# Background mode
microdetect docs --background
microdetect docs --status
microdetect docs --stop
```

### 2. `microdetect install-docs`

Installs documentation files to the user's home directory:

```bash
microdetect install-docs [--force]
```

This copies documentation files to `~/.microdetect/docs/` for offline access.

## Development Workflow for Documentation

When developing or updating documentation:

1. Edit the appropriate Markdown files in the `docs/` directory
2. Test the documentation locally using `microdetect docs`
3. Make sure to update both language versions as needed
4. Documentation changes will be included in the next package build

## Best Practices for Documentation

1. Keep documentation in sync across languages
2. Use relative links between documentation files for navigation
3. Prefix internal documentation links with language information
4. Use a consistent structure across language versions
5. Include code examples and screenshots when appropriate
6. Remember to update documentation when making significant code changes

## Testing Documentation Packaging

To test that documentation is correctly packaged:

```bash
# Build the package
python setup.py sdist bdist_wheel

# Install the package in a test environment
pip install --force-reinstall dist/microdetect-*.whl

# Start the documentation server to verify installation
microdetect docs
```

This will verify that documentation files are properly included in the build and can be accessed through the documentation server.

## Development Workflow

### Adding a New CLI Command

To add a new command to the CLI:

1. Create a new module for the functionality in an appropriate directory
2. Implement the main logic in a class or functions in this module
3. Add a function to set up the parser in `cli.py`:
   ```python
   def setup_new_command_parser(subparsers):
       """Set up parser for new command."""
       parser = subparsers.add_parser("new-command", help="Description of command")
       parser.add_argument("--required-arg", required=True, help="Required argument")
       parser.add_argument("--optional-arg", default="value", help="Optional argument")
   ```
4. Add a handler to process the command:
   ```python
   def handle_new_command(args):
       """Handle new command."""
       # Import module only when command is invoked
       from microdetect.module.new_module import NewFeature
       
       feature = NewFeature()
       result = feature.process(args.required_arg, optional_arg=args.optional_arg)
       logger.info(f"New command executed successfully: {result}")
   ```
5. Add the parser and handler to `main()`:
   ```python
   # Add to parser registration list
   setup_new_command_parser(subparsers)
   
   # Add to command switch case
   elif parsed_args.command == "new-command":
       handle_new_command(parsed_args)
   ```

### Extending Existing Features

To extend an existing feature:

1. Understand the current code and how it integrates into the workflow
2. Update existing tests or add new ones
3. Update documentation to reflect changes
4. Update the `config.yaml` file if necessary

### Update System

To extend the update system:

1. Understand the structure of `updater.py` and `aws_setup.py`
2. Add new methods for additional functionality
3. Ensure backward compatibility with the existing flow

## Code Style and Standards

MicroDetect follows these coding standards:

1. **Naming Conventions**:
   - `snake_case` for variables, functions, methods, and modules
   - `PascalCase` for classes
   - `UPPERCASE` for constants

2. **Imports Organization**:
   - Standard library imports first
   - Third-party library imports second
   - Local application imports third
   - Alphabetical sorting within each group

3. **Documentation**:
   - Module docstrings at the top of each file explaining purpose
   - Class docstrings explaining class purpose
   - Method/function docstrings in Google style

4. **Error Handling**:
   - Use specific exceptions
   - Provide meaningful error messages
   - Log errors with appropriate levels

5. **Logging**:
   - Use the `logging` module instead of print statements
   - Use appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
   - Include relevant context in log messages

## Testing

### Types of Tests

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test interaction between components
3. **Functional Tests**: Test end-to-end workflows

### Testing Guidelines

- Use `pytest` fixtures to set up test environments
- Mock external dependencies
- Use parameterized tests for multiple similar test cases
- Target 80%+ code coverage
- Include edge cases and error conditions

### Writing a Test

```python
# Example of a test for image conversion
def test_convert_tiff_to_png(sample_tiff_image, temp_output_dir):
    """Test converting a TIFF image to PNG format."""
    # Arrange
    converter = ImageConverter()
    
    # Act
    success, errors, messages = converter.convert_tiff_to_png(
        input_dir=os.path.dirname(sample_tiff_image),
        output_dir=temp_output_dir
    )
    
    # Assert
    assert success == 1
    assert errors == 0
    assert len(messages) == 0
    
    # Check that output file exists and is a valid PNG
    base_name = os.path.splitext(os.path.basename(sample_tiff_image))[0]
    output_path = os.path.join(temp_output_dir, f"{base_name}.png")
    assert os.path.exists(output_path)
    
    # Verify it's a valid PNG
    with open(output_path, 'rb') as f:
        assert f.read(8).startswith(b'\x89PNG\r\n\x1a\n')
```

## Documentation

### Documentation Structure

The documentation is organized into the following directories:

```
docs/
├── en/                          # English documentation
│   ├── index.md                 # Main entry point
│   ├── installation_guide.md    # Installation instructions
│   ├── advanced_configuration.md # Advanced configuration options
│   ├── troubleshooting.md       # Troubleshooting information
│   └── ...                      # Other documentation files
└── pt/                          # Portuguese documentation
    ├── index.md                 # Main entry point (Portuguese)
    ├── installation_guide.md    # Installation instructions (Portuguese)
    └── ...                      # Other documentation files
```

### Adding Documentation

1. Create the documentation file in both languages (if applicable)
2. Use Markdown formatting
3. Include clear section headers
4. Provide code examples when relevant
5. Add the file to the table of contents in both `index.md` files

## Build and Release Process

### Building the Package

```bash
# Update version in microdetect/__init__.py
sed -i 's/__version__ = .*/__version__ = "x.y.z"/' microdetect/__init__.py

# Create distribution
python -m build

# Check distribution
twine check dist/*
```

### Releasing to AWS CodeArtifact

The project uses GitHub Actions for automated releases to AWS CodeArtifact. When a new release is created on GitHub:

1. The workflow gets triggered
2. The package is built
3. It's uploaded to AWS CodeArtifact
4. A notification is sent

For manual uploads to AWS CodeArtifact:

```bash
# Configure AWS credentials
aws configure

# Get authorization token
export CODEARTIFACT_TOKEN=$(aws codeartifact get-authorization-token \
    --domain your-domain \
    --query authorizationToken \
    --output text)

# Get repository URL
export CODEARTIFACT_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
    --domain your-domain \
    --repository your-repository \
    --format pypi \
    --query repositoryEndpoint \
    --output text)

# Upload using twine
TWINE_USERNAME=aws \
TWINE_PASSWORD=$CODEARTIFACT_TOKEN \
python -m twine upload \
    --repository-url $CODEARTIFACT_REPOSITORY_URL \
    dist/*
```

## Common Development Tasks

### Working with Configuration

To modify configuration handling:

```python
from microdetect.utils.config import config

# Access configuration
value = config.get("section.key", default_value)

# Add new default configuration option
# In config.py, update _get_default_config method
def _get_default_config(self) -> Dict[str, Any]:
    return {
        "directories": {
            # existing settings
        },
        "new_section": {
            "new_key": "default_value"
        }
    }
```

### Implementing New Data Processing Functionality

```python
# In a new or existing module:
from typing import List, Optional, Tuple
import cv2
import numpy as np
from microdetect.utils.config import config

class NewProcessor:
    """Process images with new functionality."""
    
    def __init__(self, param1: str = None, param2: int = None):
        """
        Initialize processor with parameters.
        
        Args:
            param1: First parameter description
            param2: Second parameter description
        """
        self.param1 = param1 or config.get("new_section.param1", "default")
        self.param2 = param2 or config.get("new_section.param2", 42)
    
    def process(self, input_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Process an image with new functionality.
        
        Args:
            input_path: Path to input image
            output_path: Path to save output image (optional)
            
        Returns:
            Tuple of (success flag, output path or error message)
        """
        try:
            # Implementation
            return True, output_path
        except Exception as e:
            return False, str(e)
```

### Adding a New Training Feature

```python
# In training/train.py, add a new method:
def train_with_new_feature(self, data_yaml: str, new_param: float = 0.5) -> Dict[str, Any]:
    """
    Train a model with new feature.
    
    Args:
        data_yaml: Path to dataset YAML
        new_param: New parameter for special functionality
    
    Returns:
        Training results
    """
    # Implementation
    model = YOLO(f"yolov8{self.model_size}.pt")
    results = model.train(
        data=data_yaml,
        epochs=self.epochs,
        batch=self.batch_size,
        imgsz=self.image_size,
        # Add new parameters
        new_feature_param=new_param
    )
    
    return results
```

## Troubleshooting Development Issues

### Isolating Problems

Use separate virtual environments to test different configurations:

```bash
python -m venv venv_test
source venv_test/bin/activate
pip install -e .

# Test functionality in isolation
python -c "from microdetect.module import function; function()"
```

### Debugging Code

Use debugging libraries like `pdb` or `ipdb`:

```python
import ipdb

def problematic_function():
    # ...code...
    ipdb.set_trace()  # Breakpoint
    # ...more code...
```

Or use VSCode or PyCharm for visual debugging.

### Profiling

To identify performance bottlenecks:

```python
import cProfile
import pstats

# Run the profile
cProfile.run('function_to_profile()', 'stats.prof')

# Analyze results
p = pstats.Stats('stats.prof')
p.sort_stats('cumulative').print_stats(20)
```

## Resources for Developers

### Useful References

- [Ultralytics YOLOv8 Documentation](https://docs.ultralytics.com/)
- [PyTorch Tutorial](https://pytorch.org/tutorials/)
- [AWS CodeArtifact Documentation](https://docs.aws.amazon.com/codeartifact/)
- [PEP 8 Guide](https://peps.python.org/pep-0008/)
- [Type Hints Guide](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

### Recommended Tools

- **IDE**: VSCode or PyCharm
- **Terminal**: iTerm2 (macOS) or Windows Terminal
- **Git GUI**: GitKraken, SourceTree or VSCode Git
- **Diff Tools**: Meld or Beyond Compare
- **Data Visualization**: Matplotlib, Seaborn

## Contact and Support

For questions or support during development:

- Create an issue on GitHub
- Contact the team: dev@rodolfodebonis.com.br