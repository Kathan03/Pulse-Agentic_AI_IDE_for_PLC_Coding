# Releasing Pulse IDE

This guide explains how to create a new release of Pulse IDE.

## Prerequisites

- Git with push access to the repository
- All changes committed and pushed to `main`

## Version Numbers

Pulse uses [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., `0.1.0`, `1.0.0`, `1.2.3`)
- Pre-release versions: `1.0.0-alpha`, `1.0.0-beta.1`, `1.0.0-rc.1`

## Release Process

### 1. Update Version Numbers

Update the version in both files:

**`pulse-electron/package.json`:**
```json
{
  "version": "0.2.0"
}
```

**`src/__version__.py`:**
```python
__version__ = "0.2.0"
```

### 2. Commit Version Changes

```bash
git add pulse-electron/package.json src/__version__.py
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

### 3. Create and Push Tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

### 4. Monitor the Release

1. Go to **GitHub → Actions** tab
2. Watch the "Release" workflow run
3. Once complete, go to **Releases** page

### 5. Verify the Release

- [ ] `Pulse-Setup-0.2.0.exe` is attached
- [ ] `checksums-sha256.txt` is attached
- [ ] Release notes are generated
- [ ] Download and test the installer

## What Happens Automatically

When you push a `v*` tag, GitHub Actions:

1. **Builds the Python backend** with PyInstaller → `pulse-server.exe`
2. **Builds the Electron app** with electron-builder → `Pulse-Setup-{version}.exe`
3. **Creates a GitHub Release** with the installer attached

## Troubleshooting

### Build Failed

Check the GitHub Actions logs for errors:
1. Go to **Actions** tab
2. Click on the failed workflow run
3. Expand failed job steps

### Missing Release

Ensure your tag starts with `v`:
```bash
git tag v0.2.0   # ✓ Correct
git tag 0.2.0    # ✗ Won't trigger release
```

### Re-running a Release

To re-run a failed release:
```bash
git tag -d v0.2.0              # Delete local tag
git push origin :v0.2.0        # Delete remote tag
# Fix the issue, then:
git tag v0.2.0
git push origin v0.2.0
```
