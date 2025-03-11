# Contributing to MicroDetect

Thank you for your interest in contributing to MicroDetect! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Environment Setup](#development-environment-setup)
- [Branching Strategy](#branching-strategy)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)

## Code of Conduct

Please be respectful and considerate when contributing to this project. Treat others as you would like to be treated.

## Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/microdetect.git
   cd microdetect
   ```

2. Create a virtual environment:
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   conda create -n microdetect python=3.10
   conda activate microdetect
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install development dependencies:
   ```bash
   pip install flake8 black isort pytest pytest-cov
   ```

## Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for feature development
- Feature branches: Create from `develop` with format `feature/your-feature-name`
- Bug fixes: Create from `main` with format `fix/issue-description`

## Pull Request Process

1. Create a branch for your feature or bug fix
2. Make your changes
3. Run tests locally (`pytest`)
4. Run code formatting (`black microdetect && isort microdetect`)
5. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/)
6. Push your branch to GitHub
7. Create a Pull Request to `develop` or `main` (for hotfixes)
8. Wait for CI checks and code review
9. Address any feedback
10. Your PR will be merged once approved

## Coding Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Format code with Black (line length: 127)
- Sort imports with isort
- Use type hints where appropriate
- Document functions, classes, and modules
- Use descriptive variable and function names

## Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(annotation): add support for resuming annotation sessions

Implements a tracking system that remembers the last annotated image
and allows resuming annotation work from where it was left off.

Closes #123
```

## Testing

- Write tests for all new features and bug fixes
- Place tests in the `tests/` directory
- Run tests with `pytest`
- Ensure code coverage doesn't decrease

## Continuous Integration

This project uses GitHub Actions for Continuous Integration. The workflow performs:

1. **Linting and Code Quality Checks**
   - Checks code with flake8
   - Verifies formatting with black
   - Validates imports with isort

2. **Testing**
   - Runs tests with pytest
   - Checks code coverage
   - Tests on multiple Python versions (3.9, 3.10, 3.12)

3. **Build Verification**
   - Builds the package
   - Verifies it can be installed
   - Checks metadata and description

4. **Security Scanning**
   - Scans for security issues with bandit
   - Checks dependencies for vulnerabilities

All these checks must pass before a PR can be merged.