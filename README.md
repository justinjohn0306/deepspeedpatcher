# DeepSpeed Windows Patcher

A graphical tool to simplify building and installing DeepSpeed on Windows systems. This tool automates the build process, manages dependencies, and provides clear guidance for CUDA setup.

## Purpose

Building DeepSpeed on Windows can be challenging due to specific requirements and environment setup needs. This tool:
- Automates the build process
- Verifies system prerequisites
- Manages build environments
- Archives built wheel files
- Provides CUDA setup guidance
- Offers both build-only and build-with-install options

## System Requirements

### Mandatory Prerequisites
1. **NVIDIA GPU with CUDA Support**
   - Compatible NVIDIA GPU
   - NVIDIA Display Driver installed

2. **NVIDIA CUDA Toolkit**
   - Version 11.0 or later required
   - Must include:
     - CUDA Development Compiler (nvcc)
     - CUDA Development Libraries (CUBLAS)
     - CUDA Runtime Libraries
   - Download from: [NVIDIA CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)

3. **Visual Studio with C++ Build Tools**
   - Visual Studio 2019 or 2022 (Community Edition or BuildTools)
   - Must include "Desktop development with C++"
   - Download from: [Visual Studio Community](https://visualstudio.microsoft.com/vs/community/)

4. **Python Environment**
   - Python 3.8 or later
   - PyTorch installed with CUDA support
   - Admin rights for installation

### Python Package Dependencies
- PyTorch (must be installed manually)
- ninja (auto-installed if missing)
- psutil (auto-installed if missing)

## Startup Checks

The tool performs several verification steps on launch:

1. **Administrative Rights Check**
   - Verifies admin privileges
   - Offers to restart with elevated privileges if needed

2. **Visual Studio Detection**
   - Checks for VS2019/VS2022 installations
   - Verifies presence of C++ build tools

3. **CUDA Toolkit Verification**
   - Scans for installed CUDA versions
   - Verifies nvcc compiler availability
   - Checks CUBLAS presence

4. **Python Environment Check**
   - Verifies Python version
   - Checks PyTorch installation and CUDA availability
   - Auto-installs missing dependencies (except PyTorch)

## Usage Guide

### Building DeepSpeed

1. **Launch the Application**
   - Run as administrator
   - The tool will perform initial system checks

2. **Configure Build Settings**
   - Select DeepSpeed version
   - Choose CUDA version
   - Set installation directory
   - Configure build options (typically left unchecked for Windows)

3. **Build Options**
   - **Build Only**: Creates wheel file without installation
   - **Install Built Wheel**: Installs previously built wheel
   - **Build and Install**: Performs both operations
   - **CUDA_HOME Setup Guide**: Shows CUDA_HOME configuration instructions

### Build Management

The tool manages builds in an organized way:

1. **Work Directory Structure**
   ```
   root/
   ├── deepspeed/          # Temporary build directory
   └── deepspeed_wheels/   # Archive directory
       └── deepspeed_[version]_cuda[version]_py[version]/
           └── wheelfile.whl
   ```

2. **Cleanup Process**
   - Automatically cleans build directory before each build
   - Preserves built wheels in version-specific archives
   - Maintains separate directories for different configurations

## Configuration File (deepspeed_config.json)

The tool uses a JSON configuration file to manage available versions:

```json
{
    "versions": {
        "0.15.0": {
            "url": "https://github.com/microsoft/DeepSpeed/archive/refs/tags/v0.15.0.zip",
            "cuda_min": "11.0"
        },
        "0.15.1": {
            "url": "https://github.com/microsoft/DeepSpeed/archive/refs/tags/v0.15.1.zip",
            "cuda_min": "11.0"
        }
    }
}
```

### Adding New Versions

To add support for new DeepSpeed versions:

1. Add a new entry to the "versions" object
2. Specify the GitHub release URL
3. Set minimum CUDA version requirement

Note: This tool supports DeepSpeed 0.15.0 and later. Earlier versions may have different build requirements and are not supported.

## Additional Notes

1. **CUDA_HOME Environment**
   - The tool provides guidance for setting CUDA_HOME
   - Different options for system-wide, conda, and venv setups
   - Verification steps included

2. **Build Artifacts**
   - Wheels are archived with version information
   - Each build creates a clean environment
   - Previous builds are preserved in the archive directory

3. **Error Handling**
   - Detailed error messages in the log
   - Suggestions for common issues
   - Build process can be retried if needed

4. **Log File**
   - All operations are logged to 'deepspeed_build.log'
   - Includes timestamps and detailed progress information
   - Useful for troubleshooting

## Troubleshooting

1. **Build Failures**
   - Verify CUDA installation completeness
   - Check Visual Studio installation
   - Ensure PyTorch is installed with CUDA support
   - Review log file for specific errors

2. **CUDA Issues**
   - Confirm CUDA_HOME is set correctly
   - Verify nvcc.exe is accessible
   - Check CUDA version compatibility with PyTorch

3. **Installation Issues**
   - Run as administrator
   - Check Python environment isolation
   - Verify all prerequisites are met

## Notes for Developers

- The tool is designed for Windows 10/11 environments
- Build options are minimized for Windows compatibility
- The configuration file can be extended for future versions
- Error handling prioritizes user feedback

## Support

For DeepSpeed-specific issues, refer to:
- [DeepSpeed GitHub](https://github.com/microsoft/DeepSpeed)
- [DeepSpeed Documentation](https://www.deepspeed.ai/)

For tool-specific issues:
- Check the log file
- Verify system requirements
- Follow the CUDA setup guide
