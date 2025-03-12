# AWS CodeArtifact Setup

This document explains how to configure automatic deployment to AWS CodeArtifact and how to use the MicroDetect package from the private repository.

## Table of Contents
- [Requirements](#requirements)
- [AWS CodeArtifact Configuration](#aws-codeartifact-configuration)
  - [1. Create a CodeArtifact Domain](#1-create-a-codeartifact-domain)
  - [2. Create a CodeArtifact Repository](#2-create-a-codeartifact-repository)
  - [3. Connect the Repository to PyPI](#3-connect-the-repository-to-pypi)
  - [4. Create IAM User with Permissions](#4-create-iam-user-with-permissions)
  - [5. Generate Access Key for IAM User](#5-generate-access-key-for-iam-user)
- [GitHub Configuration](#github-configuration)
  - [1. Add Secrets to GitHub Repository](#1-add-secrets-to-github-repository)
- [Workflow Usage](#workflow-usage)
  - [Automatic Publication on New Releases](#automatic-publication-on-new-releases)
  - [Manual Publication](#manual-publication)
- [Installing the Package from AWS CodeArtifact](#installing-the-package-from-aws-codeartifact)
  - [1. Configure pip to Use AWS CodeArtifact](#1-configure-pip-to-use-aws-codeartifact)
  - [2. Install the Package](#2-install-the-package)
  - [3. Manual pip Configuration](#3-manual-pip-configuration)
- [MicroDetect's AWS Configuration Tool](#microdetects-aws-configuration-tool)
- [Troubleshooting](#troubleshooting)
  - [Authentication Error](#authentication-error)
  - [Version Error](#version-error)
  - [Dependency Error](#dependency-error)

## Requirements

To configure automatic deployment, you will need:

1. An AWS account with permissions to access CodeArtifact
2. A domain and repository in CodeArtifact
3. AWS credentials with permissions to publish to the repository
4. Secrets configured in GitHub (for CI/CD)

## AWS CodeArtifact Configuration

### 1. Create a CodeArtifact Domain

If you don't already have a domain, create one:

```bash
aws codeartifact create-domain --domain your-domain
```

### 2. Create a CodeArtifact Repository

Create a repository within your domain:

```bash
aws codeartifact create-repository \
    --domain your-domain \
    --repository your-repository \
    --description "Private Python repository for MicroDetect"
```

### 3. Connect the Repository to PyPI

To allow your repository to access packages from the public PyPI:

```bash
# Create a repository to proxy PyPI
aws codeartifact create-repository \
    --domain your-domain \
    --repository pypi-store \
    --description "Proxy for public PyPI"

# Connect to external PyPI
aws codeartifact associate-external-connection \
    --domain your-domain \
    --repository pypi-store \
    --external-connection public:pypi

# Make your repository use pypi-store as an upstream
aws codeartifact update-repository \
    --domain your-domain \
    --repository your-repository \
    --upstreams repositoryName=pypi-store
```

### 4. Create IAM User with Permissions

Create a user with appropriate permissions:

```bash
aws iam create-user --user-name codeartifact-publisher

aws iam attach-user-policy --user-name codeartifact-publisher \
    --policy-arn arn:aws:iam::aws:policy/AWSCodeArtifactAdminAccess
```

### 5. Generate Access Key for IAM User

Generate credentials for the IAM user:

```bash
aws iam create-access-key --user-name codeartifact-publisher
```

Save the returned `AccessKeyId` and `SecretAccessKey`.

## GitHub Configuration

### 1. Add Secrets to GitHub Repository

Go to Settings → Secrets → Actions in your repository and add the following secrets:

- `AWS_ACCESS_KEY_ID`: The access key ID of the IAM user
- `AWS_SECRET_ACCESS_KEY`: The secret access key of the IAM user
- `AWS_REGION`: The region where CodeArtifact is hosted (e.g., `us-east-1`)
- `AWS_CODEARTIFACT_DOMAIN`: The name of the CodeArtifact domain
- `AWS_CODEARTIFACT_REPOSITORY`: The name of the CodeArtifact repository
- `AWS_CODEARTIFACT_OWNER`: (Optional) The AWS account ID that owns the domain
- `GH_TOKEN`: GitHub personal access token with repository permissions
- `BOTTOKEN`: Your Telegram bot token
- `CHAT_ID`: Chat ID for notifications
- `THREAD_ID`: (Optional) Thread ID for notifications in groups

## Workflow Usage

### Automatic Publication on New Releases

When you create a new release on GitHub, the workflow is automatically triggered and:

1. Gets release information
2. Updates the version in the code (`__version__`)
3. Builds the package
4. Publishes to AWS CodeArtifact
5. Notifies via Telegram with the result

### Manual Publication

You can also trigger the workflow manually:

1. Go to the "Actions" tab on GitHub
2. Select "Deploy to AWS CodeArtifact"
3. Click "Run workflow"
4. Choose the version increment type (patch, minor, major) or specify a custom version
5. Click "Run workflow"

## Installing the Package from AWS CodeArtifact

### 1. Configure pip to Use AWS CodeArtifact

```bash
# Get authorization token (valid for 12 hours)
aws codeartifact login \
    --tool pip \
    --domain your-domain \
    --repository your-repository \
    --domain-owner ACCOUNT_ID
```

### 2. Install the Package

```bash
pip install microdetect
```

### 3. Manual pip Configuration

Alternatively, you can configure pip manually:

```bash
# Get token
export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain your-domain \
    --domain-owner ACCOUNT_ID \
    --query authorizationToken \
    --output text)

# Get repository URL
export CODEARTIFACT_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
    --domain your-domain \
    --domain-owner ACCOUNT_ID \
    --repository your-repository \
    --format pypi \
    --query repositoryEndpoint \
    --output text)

# Install the package
pip install microdetect \
    --index-url "${CODEARTIFACT_REPOSITORY_URL}simple/" \
    --extra-index-url https://pypi.org/simple
```

## MicroDetect's AWS Configuration Tool

MicroDetect provides a CLI tool to simplify AWS CodeArtifact configuration:

```bash
# Set up AWS CodeArtifact
microdetect setup-aws --domain your-domain --repository your-repository --configure-aws

# Available options:
#   --domain           CodeArtifact domain name (required)
#   --repository       CodeArtifact repository name (required)
#   --domain-owner     AWS account ID that owns the domain (optional)
#   --region           AWS region (default: us-east-1)
#   --configure-aws    Configure AWS credentials
#   --test             Test connection after configuration
```

This tool will:
1. Check if AWS CLI is installed (installing it if necessary)
2. Configure AWS credentials if requested
3. Set up environment variables and configuration for MicroDetect's update system
4. Test the connection to ensure everything works

## Troubleshooting

### Authentication Error

If you receive authentication errors:

1. Check if your AWS credentials are correct
2. Verify that the authorization token is valid (expires after 12 hours)
3. Check the IAM user's permissions

```bash
# Test authentication
aws sts get-caller-identity

# Regenerate authorization token
aws codeartifact get-authorization-token \
    --domain your-domain \
    --query authorizationToken \
    --output text
```

### Version Error

If you try to publish a version that already exists:

1. Make sure to increment the version before publishing
2. Check the current version in the repository:

```bash
pip index versions microdetect \
    --index-url "${CODEARTIFACT_REPOSITORY_URL}simple/" \
    --no-cache-dir
```

### Dependency Error

If there are issues with dependencies:

1. Make sure your repository has access to the public PyPI
2. Check that all dependencies are correctly listed in `setup.py` or `requirements.txt`

```bash
# Verify upstream configuration
aws codeartifact list-repositories-in-domain \
    --domain your-domain

# Check repository details including upstreams
aws codeartifact describe-repository \
    --domain your-domain \
    --repository your-repository
```

For more detailed troubleshooting, please refer to the [AWS CodeArtifact Documentation](https://docs.aws.amazon.com/codeartifact/latest/ug/welcome.html) or check the [Troubleshooting Guide](troubleshooting.md).