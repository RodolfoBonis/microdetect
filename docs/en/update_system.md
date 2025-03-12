# MicroDetect Update System

This document explains the automatic update system in MicroDetect, which allows you to check for and install updates from AWS CodeArtifact.

## Overview

MicroDetect's update system enables you to:

1. Configure a connection to AWS CodeArtifact
2. Check for newer versions available
3. Update to the latest version securely
4. Receive automatic notifications about new versions

## Prerequisites

To use the update system, you will need:

- Access to an AWS CodeArtifact domain and repository
- AWS CLI installed (will be installed automatically if needed)
- AWS credentials with permissions to access CodeArtifact

## Initial Setup

Before using the update system, you need to configure the connection to AWS CodeArtifact:

```bash
microdetect setup-aws --domain your-domain --repository your-repository --configure-aws
```

### Configuration Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--domain` | AWS CodeArtifact domain name | Yes |
| `--repository` | AWS CodeArtifact repository name | Yes |
| `--domain-owner` | ID of the account that owns the domain | No |
| `--region` | AWS region (default: us-east-1) | No |
| `--configure-aws` | Configure AWS credentials | No |
| `--test` | Test the connection after configuration | No |

### Complete Setup Example

```bash
microdetect setup-aws --domain my-domain --repository my-repo --domain-owner 123456789012 --region us-east-2 --configure-aws --test
```

## Checking for Updates

To manually check for available updates:

```bash
microdetect update --check-only
```

This command compares the installed version with the latest version available in AWS CodeArtifact and informs you if an update is available.

## Installing Updates

To update MicroDetect to the latest version:

```bash
microdetect update
```

When you run this command:

1. The system checks if there's a new version available
2. If a new version is found, you'll be asked if you want to update
3. The update is downloaded and installed using pip
4. The update process displays progress in real-time

### Forcing an Update

To update without confirmation:

```bash
microdetect update --force
```

## Automatic Update Checks

MicroDetect automatically checks for available updates after running any command (except the update commands themselves). If an update is found, you'll see a notification:

```
🔄 New MicroDetect version available: 1.2.3 (current: 1.1.0)
   To update, run: microdetect update
```

### Disabling Automatic Checks

If you don't want to check for updates automatically, you can set the `MICRODETECT_SKIP_UPDATE_CHECK` environment variable:

```bash
# Linux/macOS
export MICRODETECT_SKIP_UPDATE_CHECK=1

# Windows
set MICRODETECT_SKIP_UPDATE_CHECK=1
```

## Using with Makefile

The project's Makefile includes commands to help manage updates:

```bash
# Configure AWS CodeArtifact
make setup-aws DOMAIN=your-domain REPOSITORY=your-repo

# Check for updates
make check-update

# Update application
make update
```

## How It Works Internally

The update system operates as follows:

1. **Authentication with AWS CodeArtifact**:
   - Obtains an authentication token using AWS CLI
   - Determines the repository endpoint

2. **Version Checking**:
   - Uses pip to list available versions
   - Extracts and compares versions using semantic versioning

3. **Configuration Sources**:
   - Looks for AWS credentials in multiple locations in this order:
     1. Environment variables (`AWS_CODEARTIFACT_DOMAIN`, `AWS_CODEARTIFACT_REPOSITORY`, `AWS_CODEARTIFACT_OWNER`)
     2. Configuration file at `~/.microdetect/config.ini`
     3. Local `.env` file (for compatibility)

4. **Update Process**:
   - Sets up pip environment to use AWS CodeArtifact repository
   - Runs the update preserving dependencies
   - Detects if running in a Conda environment and adjusts accordingly

5. **Check Caching**:
   - Stores the last check date to avoid overloading
   - Checks only once per day (configurable)

## Troubleshooting

### AWS Configuration Error

If you receive a connection error to AWS CodeArtifact:

1. Check if your AWS credentials are configured correctly
2. Check if the domain and repository exist
3. Check if you have permissions to access the repository
4. Run `microdetect setup-aws --test` to diagnose issues

### Version Check Error

If you can't check or get the latest version:

1. Check if the AWS token is valid
2. Check if the package exists in the repository
3. Check your internet connection

### Update Error

If the update fails:

1. Check if you have permissions to install packages
2. Try updating with pip directly
3. Check for dependency conflicts

## Logging and Diagnostics

The update system logs detailed information to the MicroDetect log file. To see more detailed logs, you can increase the logging level:

```bash
export MICRODETECT_LOG_LEVEL=DEBUG
microdetect update --check-only
```

The logs will help diagnose issues in the update process.

## Common Questions

### How often does MicroDetect check for updates?

By default, MicroDetect checks for updates once per day when you run any command. The check interval can be configured in the `config.yaml` file.

### Can I update to a specific version?

Yes, you can update to a specific version using:

```bash
microdetect update --version 1.2.3
```

### How do I know which version I'm currently using?

You can check your current version with:

```bash
microdetect --version
```

### What happens if an update fails?

If an update fails, MicroDetect will keep the current version and display an error message. You can try again or check the logs for more information.

### Can I roll back to a previous version?

Yes, you can install a specific previous version using:

```bash
microdetect update --version 1.1.0
```

## Best Practices

1. **Regular Updates**: Keep MicroDetect updated to benefit from the latest features and bug fixes.
2. **Test After Updates**: After updating to a new version, test your workflows to ensure everything works as expected.
3. **Backup Important Data**: Before major version updates, backup your configuration and important data.
4. **Update in Development First**: If using MicroDetect in production, test updates in a development environment first.
5. **Check Release Notes**: Review release notes before updating to understand the changes in the new version.