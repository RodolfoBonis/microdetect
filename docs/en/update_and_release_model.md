# Update and Release Model

This document explains the update system and version lifecycle for MicroDetect, describing how the project is versioned, updated, and distributed.

## Table of Contents
- [Versioning Strategy](#versioning-strategy)
- [Distribution Channels](#distribution-channels)
- [Release Types](#release-types)
- [Development Lifecycle](#development-lifecycle)
- [Automatic Update System](#automatic-update-system)
- [Release Cycle and Frequency](#release-cycle-and-frequency)
- [Technical Implementation](#technical-implementation)
- [Version Support Policy](#version-support-policy)
- [Changelog and Documentation](#changelog-and-documentation)
- [Rollback and Recovery](#rollback-and-recovery)

## Versioning Strategy

MicroDetect follows [Semantic Versioning](https://semver.org/) (SemVer) principles, using a three-number versioning scheme in the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incremented for incompatible changes with previous versions
- **MINOR**: Incremented for backward-compatible functionality additions
- **PATCH**: Incremented for backward-compatible bug fixes

### Examples:

- `1.0.0`: Initial stable version
- `1.1.0`: Addition of new features
- `1.1.1`: Bug fixes to version 1.1.0
- `2.0.0`: Changes that break compatibility with versions 1.x.x

## Distribution Channels

MicroDetect is distributed through two main channels:

1. **AWS CodeArtifact**: Private repository for controlled distribution
2. **GitHub Releases**: Packages and source code for each version

### AWS CodeArtifact

CodeArtifact is used as a private Python repository, allowing:

- Access control for internal distribution or specific customers
- Rapid update distribution
- Strict versioning
- Automatic update verification

### GitHub Releases

For each stable version, we create:

- A Git tag with the version number
- A GitHub Release with detailed release notes
- Assets containing the source code and packaged distributions

## Release Types

### Major Releases (X.0.0)

- Significant changes with possible compatibility breaks
- New architectures or important refactorings
- API changes that are not backward compatible
- Longer development and testing cycle
- Prior announcement and transition period

### Minor Releases (0.X.0)

- New backward-compatible features
- Performance improvements
- Addition of new commands or options
- Expansion of existing features

### Patch Releases (0.0.X)

- Bug fixes
- Small improvements
- Documentation updates
- Minor optimizations

### Pre-releases

For development versions, we use suffixes:

- `1.2.0-alpha.1`: Very unstable, for initial testing
- `1.2.0-beta.1`: Reasonably stable, for wider testing
- `1.2.0-rc.1`: Release candidate, for final testing

## Development Lifecycle

### 1. Planning

- Scope and requirements definition
- Creation of issues and milestones on GitHub
- Prioritization of features and fixes

### 2. Development

- Implementation in specific branches
- Unit and integration tests
- Code review through Pull Requests

### 3. Testing

- Internal alpha testing
- Beta testing with selected users
- Performance and usability validation

### 4. Release

- Building distribution packages
- Documentation and changelog updates
- Publication on AWS CodeArtifact and GitHub

### 5. Maintenance

- Monitoring and feedback collection
- Reported bug fixes
- Planning for future improvements

## Automatic Update System

MicroDetect includes an automatic update system that:

1. Periodically checks for availability of new versions
2. Notifies users about available updates
3. Allows updating with a single command

### Update Flow

1. **Verification**: The system checks AWS CodeArtifact for newer versions
2. **Notification**: If a new version is found, the user is notified
3. **Confirmation**: The user decides whether to update
4. **Download and Installation**: The new version is downloaded and installed
5. **Verification**: The system confirms that the update was successful

### Check Configuration

Users can configure the checking behavior:

- Disable automatic checks
- Change the checking frequency
- Opt for automatic updates without confirmation

## Release Cycle and Frequency

### Version Planning

- **Major releases**: Once or twice a year
- **Minor releases**: Every 1-2 months
- **Patch releases**: As needed (typically weekly)

### Release Notification

Releases are announced through:

- In-app notifications
- Telegram messages for subscribers
- GitHub Releases

## Technical Implementation

### Release Automation

The release process is automated using GitHub Actions:

1. A PR is merged into the main branch
2. CI validates the change
3. The auto-release workflow is triggered
4. Based on commit messages, the version is incremented
5. A new tag and release are created on GitHub
6. The package is built and sent to AWS CodeArtifact

```yaml
# Excerpt from auto-release.yml workflow
determine_version:
  steps:
    - name: Analyze PR for version type
      id: analyze_pr
      run: |
        # Determine version type based on labels or commit messages
        if echo "$pr_data" | grep -i -q '"title":.*\(feat\|feature\|enhancement\)'; then
          echo "Detected feature from PR title, using minor version"
          echo "version_type=minor" >> $GITHUB_OUTPUT
        elif echo "$pr_data" | grep -i -q '"title":.*\(fix\|bugfix\|patch\)'; then
          echo "Detected bugfix from PR title, using patch version"
          echo "version_type=patch" >> $GITHUB_OUTPUT
        else
          echo "No specific version indicator found, using patch as default"
          echo "version_type=patch" >> $GITHUB_OUTPUT
        fi
```

### Update System

The update system uses:

1. AWS CodeArtifact for package storage
2. Temporary authentication tokens for secure access
3. pip for package installation
4. Semantic version comparison

```python
# Excerpt from updater.py
def compare_versions(current: str, latest: str) -> bool:
    # Split versions into parts (major, minor, patch)
    current_parts = [int(part) for part in current.split('.')]
    latest_parts = [int(part) for part in latest.split('.')]
    
    # Compare each version part
    for i in range(len(current_parts)):
        if latest_parts[i] > current_parts[i]:
            return True
        elif latest_parts[i] < current_parts[i]:
            return False
    
    return False
```

## Version Support Policy

### Long-Term Support (LTS)

- LTS versions are designated with the `-lts` suffix (e.g., `1.0.0-lts`)
- LTS versions receive security fixes for 12 months
- Critical bug fixes for 8 months
- Documentation kept updated

### Regular Versions

- Non-LTS versions receive security fixes for 3 months
- Critical bug fixes for 2 months
- Users are encouraged to update to the latest version

### End of Support

When a version reaches end of support:

- Notifications are sent to users
- Documentation is archived
- No more fixes are issued
- Update verification resources continue to work

## Changelog and Documentation

### Changelog

Each release includes a detailed changelog, automatically generated from commit messages and manually refined, including:

- New features
- Bug fixes
- Performance improvements
- API changes
- Migration notes (when applicable)

### Version Documentation

Documentation is updated with each release, including:

- User guides
- Examples
- API reference
- Behavior changes
- Migration notes

## Rollback and Recovery

For situations where an update causes problems, we have rollback strategies:

### Manual Rollback

Users can revert to a previous version:

```bash
# Install a specific version
microdetect update --version 1.1.0
```

### Isolated Environments

For testing new versions without affecting the production environment:

```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate
pip install microdetect==2.0.0
```

## Using the Update System

### Checking for Updates

To manually check for available updates:

```bash
microdetect update --check-only
```

This command will show information about the current version and indicate if a newer version is available.

### Updating MicroDetect

To update MicroDetect to the latest version:

```bash
microdetect update
```

The update process will:
1. Check for a newer version
2. Ask for confirmation before updating
3. Download and install the new version
4. Display the update progress

### Forcing an Update

To update without confirmation:

```bash
microdetect update --force
```

### AWS CodeArtifact Configuration

Before using the update system, you need to configure AWS CodeArtifact:

```bash
microdetect setup-aws --domain your-domain --repository your-repository --configure-aws
```

You'll need to provide:
- AWS access credentials
- CodeArtifact domain name
- Repository name
- Region (optional)

### Disabling Automatic Update Checks

If you don't want automatic update checks, set the environment variable:

```bash
# Linux/macOS
export MICRODETECT_SKIP_UPDATE_CHECK=1

# Windows
set MICRODETECT_SKIP_UPDATE_CHECK=1
```

## Conclusion

The MicroDetect update and release model is designed to:

1. Deliver new features and fixes regularly
2. Maintain stability for existing users
3. Provide a clear migration path between versions
4. Facilitate the update process
5. Clearly communicate changes in each version

This model balances the need for rapid software evolution with the stability required by users in production environments.