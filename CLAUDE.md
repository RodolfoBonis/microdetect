# MicroDetect Development Guide

## Build/Test/Lint Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Run all tests**: `pytest tests`
- **Run single test**: `pytest tests/path/to/test_file.py::TestClass::test_function -v`
- **Run with coverage**: `pytest --cov=microdetect tests`
- **Lint code**: `tox -e lint`
- **Format code**: `black microdetect tests`
- **Run type checking**: `mypy --install-types --non-interactive microdetect`

## Code Style Guidelines

- **Line length**: 127 characters max
- **Imports**: Use `isort` with Black profile
- **Formatting**: Follow Black formatting style
- **Type hints**: Use proper type annotations from `typing` module
- **Docstrings**: All functions/classes need docstrings with Args/Returns sections
- **Error handling**: Use try/except with specific exceptions and proper logging
- **Naming**: Use snake_case for functions/variables, PascalCase for classes
- **Logging**: Use the module-level logger for all logging operations
- **Testing**: Write unit tests for all new functionality

## Additional Notes

- Run `tox` for full test suite across supported Python versions (3.9-3.12)
- Documentation built with MkDocs (`mkdocs build`)
- PR submissions should pass all CI tests
- Update docs on `docs` directory with new functionality and examples
- Use `black` and `isort` before committing changes
- Update Docs when adding new functionality or modifying existing code
- Use `conda activate yeast_detection` to activate the virtual environment and run any python commands
- The Tests files should be named as `test_<name>.py` and the test functions should be named as `test_<name>`
- The test functions should be written in the same order as the functions in the main code
- The Test files are present in the `tests` directory
- All installation commands run with `--index-url https://pypi.org/simple` to avoid any package installation issues