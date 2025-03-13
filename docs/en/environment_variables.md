# Environment Variables Guide

This guide explains the environment variables supported by MicroDetect, which provide an alternative way to configure the application without modifying the configuration file.

## Table of Contents
- [Introduction](#introduction)
- [Core Environment Variables](#core-environment-variables)
- [AWS CodeArtifact Variables](#aws-codeartifact-variables)
- [Hardware Configuration Variables](#hardware-configuration-variables)
- [Logging Variables](#logging-variables)
- [Directory Variables](#directory-variables)
- [Setting Environment Variables](#setting-environment-variables)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)
  - [In Python Scripts](#in-python-scripts)
- [Environment Variables in Docker](#environment-variables-in-docker)
- [Environment Variables in CI/CD](#environment-variables-in-cicd)
- [Configuration Priority](#configuration-priority)
- [Best Practices](#best-practices)

## Introduction

Environment variables provide a flexible way to configure MicroDetect without modifying the configuration file. They are particularly useful in:

- CI/CD pipelines
- Docker containers
- Automated scripts
- Multiple environments (development, staging, production)
- Situations where you need to temporarily override settings

MicroDetect checks for specific environment variables at startup and uses them to override corresponding settings in the configuration file.

## Core Environment Variables

These environment variables control fundamental aspects of MicroDetect:

| Variable | Description | Default |
|----------|-------------|---------|
| `MICRODETECT_CONFIG_PATH` | Path to the configuration file | `./config.yaml` |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Disable automatic update check | Not set |
| `MICRODETECT_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MICRODETECT_CACHE_DIR` | Cache directory | `~/.cache/microdetect` |
| `MICRODETECT_DATASET_DIR` | Dataset directory | `./dataset` |
| `MICRODETECT_IMAGES_DIR` | Images directory | `./data/images` |
| `MICRODETECT_LABELS_DIR` | Labels directory | `./data/labels` |
| `MICRODETECT_OUTPUT_DIR` | Output directory | `./runs/train` |
| `MICRODETECT_REPORTS_DIR` | Reports directory | `./reports` |
| `MICRODETECT_NO_INTERACTIVE` | Disable interactive features | Not set |

Example usage:
```bash
MICRODETECT_LOG_LEVEL=DEBUG microdetect train --dataset_dir dataset
```

## AWS CodeArtifact Variables

These variables control the AWS CodeArtifact integration for updates:

| Variable | Description |
|----------|-------------|
| `AWS_CODEARTIFACT_DOMAIN` | AWS CodeArtifact domain name |
| `AWS_CODEARTIFACT_REPOSITORY` | AWS CodeArtifact repository name |
| `AWS_CODEARTIFACT_OWNER` | AWS account ID that owns the domain |
| `AWS_REGION` | AWS region for CodeArtifact (default: us-east-1) |
| `AWS_ACCESS_KEY_ID` | AWS access key ID for authentication |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key for authentication |
| `AWS_SESSION_TOKEN` | AWS session token (if using temporary credentials) |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Set to `1` to disable update checks |

Example usage:
```bash
export AWS_CODEARTIFACT_DOMAIN=my-domain
export AWS_CODEARTIFACT_REPOSITORY=my-repo
export AWS_REGION=us-west-2
microdetect update --check-only
```

## Hardware Configuration Variables

These variables control how MicroDetect uses hardware resources:

| Variable | Description | Default |
|----------|-------------|---------|
| `CUDA_VISIBLE_DEVICES` | GPUs to use (e.g., "0,1,2") | All available |
| `MICRODETECT_DEVICE` | Device to use (e.g., "cpu", "0", "cuda:0") | Auto-detect |
| `OMP_NUM_THREADS` | OpenMP threads for CPU operations | Number of CPUs |
| `MKL_NUM_THREADS` | MKL threads for CPU operations | Number of CPUs |
| `NUMEXPR_NUM_THREADS` | NumExpr threads for CPU operations | Number of CPUs |
| `MICRODETECT_BATCH_SIZE` | Override default batch size | Varies by command |
| `MICRODETECT_WORKERS` | Number of data loading workers | `8` |

Example usage:
```bash
# Use only the first GPU
CUDA_VISIBLE_DEVICES=0 microdetect train --dataset_dir dataset

# Use CPU instead of GPU
MICRODETECT_DEVICE=cpu microdetect train --dataset_dir dataset

# Set CPU parallelism
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 microdetect train --dataset_dir dataset
```

## Logging Variables

These variables control logging behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `MICRODETECT_LOG_LEVEL` | Logging level | `INFO` |
| `MICRODETECT_LOG_FILE` | Log file path | `microdetect.log` |
| `MICRODETECT_LOG_FORMAT` | Log message format | See [Configuration Reference](configuration_reference.md) |
| `MICRODETECT_LOG_MAX_SIZE` | Maximum log file size in bytes | `10485760` (10MB) |
| `MICRODETECT_LOG_BACKUP_COUNT` | Number of log backups to keep | `3` |
| `MICRODETECT_NO_COLOR` | Disable colored console output | Not set |

Example usage:
```bash
MICRODETECT_LOG_LEVEL=DEBUG MICRODETECT_LOG_FILE=debug.log microdetect train --dataset_dir dataset
```

## Directory Variables

These variables control the directories used by MicroDetect:

| Variable | Description | Default |
|----------|-------------|---------|
| `MICRODETECT_DATASET_DIR` | Dataset directory | `./dataset` |
| `MICRODETECT_IMAGES_DIR` | Images directory | `./data/images` |
| `MICRODETECT_LABELS_DIR` | Labels directory | `./data/labels` |
| `MICRODETECT_OUTPUT_DIR` | Output directory | `./runs/train` |
| `MICRODETECT_REPORTS_DIR` | Reports directory | `./reports` |
| `MICRODETECT_CACHE_DIR` | Cache directory | `~/.cache/microdetect` |
| `MICRODETECT_CONFIG_DIR` | Configuration directory | `~/.microdetect` |

Example usage:
```bash
MICRODETECT_IMAGES_DIR=/path/to/images MICRODETECT_LABELS_DIR=/path/to/labels microdetect dataset --dataset_dir dataset
```

## Setting Environment Variables

### Linux/macOS

Temporary (for current terminal session):
```bash
export MICRODETECT_LOG_LEVEL=DEBUG
export MICRODETECT_CACHE_DIR=/tmp/microdetect_cache
```

Permanent (add to ~/.bashrc or ~/.zshrc):
```bash
echo 'export MICRODETECT_LOG_LEVEL=DEBUG' >> ~/.bashrc
source ~/.bashrc
```

One-time (for a single command):
```bash
MICRODETECT_LOG_LEVEL=DEBUG microdetect train --dataset_dir dataset
```

### Windows

Temporary (for current command prompt):
```cmd
set MICRODETECT_LOG_LEVEL=DEBUG
set MICRODETECT_CACHE_DIR=C:\temp\microdetect_cache
```

Permanent (using System Properties):
1. Right-click on Computer → Properties → Advanced system settings
2. Click on Environment Variables
3. Add or modify variables in User variables or System variables section

One-time (for a single command):
```cmd
set MICRODETECT_LOG_LEVEL=DEBUG && microdetect train --dataset_dir dataset
```

In PowerShell:
```powershell
$env:MICRODETECT_LOG_LEVEL = "DEBUG"
microdetect train --dataset_dir dataset
```

### In Python Scripts

To set environment variables in Python scripts:

```python
import os
import subprocess

# Set environment variables
os.environ["MICRODETECT_LOG_LEVEL"] = "DEBUG"
os.environ["MICRODETECT_CACHE_DIR"] = "/tmp/microdetect_cache"

# Run MicroDetect as a subprocess
subprocess.run(["microdetect", "train", "--dataset_dir", "dataset"])

# Or import and use MicroDetect directly
from microdetect.training import YOLOTrainer
trainer = YOLOTrainer()  # Will use the environment variables
trainer.train("dataset/data.yaml")
```

## Environment Variables in Docker

When running MicroDetect in Docker containers, you can set environment variables using the `-e` flag:

```bash
docker run -e MICRODETECT_LOG_LEVEL=DEBUG -e CUDA_VISIBLE_DEVICES=0 microdetect-image microdetect train --dataset_dir dataset
```

Or in a Docker Compose file:

```yaml
version: '3'
services:
  microdetect:
    image: microdetect-image
    environment:
      - MICRODETECT_LOG_LEVEL=DEBUG
      - CUDA_VISIBLE_DEVICES=0
      - AWS_CODEARTIFACT_DOMAIN=my-domain
      - AWS_CODEARTIFACT_REPOSITORY=my-repo
```

## Environment Variables in CI/CD

In CI/CD pipelines, environment variables are often set in the configuration file:

GitHub Actions example:
```yaml
jobs:
  train_model:
    runs-on: ubuntu-latest
    env:
      MICRODETECT_LOG_LEVEL: INFO
      MICRODETECT_NO_INTERACTIVE: 1
      AWS_CODEARTIFACT_DOMAIN: ${{ secrets.AWS_CODEARTIFACT_DOMAIN }}
      AWS_CODEARTIFACT_REPOSITORY: ${{ secrets.AWS_CODEARTIFACT_REPOSITORY }}
    steps:
      - uses: actions/checkout@v3
      - name: Train model
        run: microdetect train --dataset_dir dataset --model_size m --epochs 100
```

GitLab CI example:
```yaml
train_job:
  stage: train
  variables:
    MICRODETECT_LOG_LEVEL: INFO
    MICRODETECT_NO_INTERACTIVE: 1
  script:
    - microdetect train --dataset_dir dataset --model_size m --epochs 100
```

## Configuration Priority

MicroDetect uses the following order of priority to determine the final configuration:

1. Command line arguments (highest priority)
2. Environment variables
3. Configuration file
4. Internal default values (lowest priority)

For example, if you set the batch size in all three ways:
- Command line: `microdetect train --batch_size 16`
- Environment: `MICRODETECT_BATCH_SIZE=32`
- Config file: `batch_size: 64` in `config.yaml`

The command line value (16) will be used because it has the highest priority.

## Best Practices

1. **Use environment variables for temporary changes**: For permanent changes, modify the configuration file.

2. **Use environment variables in CI/CD pipelines**: This allows for different configurations in different environments without modifying files.

3. **Use environment variables for secrets**: Never store AWS credentials or other secrets in configuration files.

4. **Document your environment variables**: Include a list of required and optional environment variables in your project documentation.

5. **Set related variables together**: Some variables work together (like `OMP_NUM_THREADS` and `MKL_NUM_THREADS`), so set them consistently.

6. **Use descriptive names for scripts**: Create shell scripts with descriptive names for common environment variable combinations.

7. **Check for environment variable conflicts**: Be aware that some environment variables might be set by other software or the system.

8. **Consider using `.env` files**: For development, store environment variables in a `.env` file and load them as needed (not for secrets in production).