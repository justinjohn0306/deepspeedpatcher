import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import platform
import subprocess
import sys
import time
import shutil
import ctypes
import requests
import winreg
import webbrowser
import json
from pathlib import Path
from importlib.metadata import distribution, PackageNotFoundError

class DeepSpeedPatcher:
    def __init__(self):
        # Check admin rights first
        if not self.check_admin():
            if messagebox.askyesno(
                "Admin Rights Required",
                "This application requires administrative privileges to build DeepSpeed. "
                "Would you like to restart with admin rights?"
            ):
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable,
                    f'"{os.path.abspath(__file__)}"', None, 1
                )
                sys.exit()
            else:
                sys.exit()
        
        # Load configuration
        try:
            with open('deepspeed_config.json', 'r') as f:
                self.config = json.load(f)
                self.available_versions = list(sorted(self.config['versions'].keys()))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            sys.exit(1)

        # Initialize main window
        self.root = tk.Tk()        
        self.root.title("DeepSpeed Windows Patcher")
        self.root.geometry("1400x970")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Get Python version
        self.python_version = platform.python_version()
                   
        # Get PyTorch version and CUDA info
        try:
            import torch
            self.torch_version = torch.__version__
            self.torch_cuda = f"CUDA {torch.version.cuda}" if torch.cuda.is_available() else "CPU only"
        except ImportError:
            self.torch_version = "Not installed"
            self.torch_cuda = "N/A"
                
        # Get available CUDA versions
        self.cuda_versions = self.get_available_cuda_versions()

        # Style configuration
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Info.TLabel', font=('Helvetica', 12))
        style.configure("Big.TButton", font=("Helvetica", 12), padding=10)

        # Initialize log file
        self.log_file = open('deepspeed_build.log', 'w', encoding='utf-8', buffering=1)

        # Create GUI
        self.create_gui()
        
        # Initial log message
        self.log("DeepSpeed Windows Patcher Started")
        
        # Perform initial system checks
        self.check_prerequisites()
            
    def log(self, message):
        """Add message to log area and file with timestamp"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        # Write to GUI
        self.log_area.insert(tk.END, log_message)
        self.log_area.see(tk.END)
        
        # Write to file
        try:
            self.log_file.write(log_message)
            self.log_file.flush()  # Force write to disk
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        # Process pending events to keep GUI responsive
        self.root.update()
        self.root.update_idletasks()
        
    def get_available_cuda_versions(self):
        """Find installed CUDA versions"""
        cuda_base = "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA"
        versions = []
        if os.path.exists(cuda_base):
            for item in os.listdir(cuda_base):
                if item.startswith('v'):
                    versions.append(item[1:])  # Remove 'v' prefix
        return sorted(versions, reverse=True)
    
    def browse_directory(self):
        """Open directory browser"""
        directory = filedialog.askdirectory()
        if directory:
            self.install_dir_var.set(directory)

    def check_admin(self):
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def create_gui(self):
        """Create the main GUI interface"""
        # Configure grid weights for main window
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)       
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(1, weight=1)  # Make column 1 expandable
               
        # Progress variables
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to start...")

        # Environment Information Frame
        info_frame = ttk.LabelFrame(main_frame, text="Build Environment", padding="5")
        info_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(info_frame, text=f"Python: {self.python_version}", style='Info.TLabel').grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(info_frame, text=f"PyTorch: {self.torch_version} ({self.torch_cuda})", style='Info.TLabel').grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Version selection
        ttk.Label(main_frame, text="DeepSpeed Version:", style='Header.TLabel').grid(row=1, column=0, pady=5, sticky=tk.W)
        self.version_var = tk.StringVar(value=self.available_versions[-1] if self.available_versions else "")
        version_combo = ttk.Combobox(main_frame, textvariable=self.version_var, values=self.available_versions)
        version_combo.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # CUDA selection with dropdown
        ttk.Label(main_frame, text="CUDA ToolKit Version:", style='Header.TLabel').grid(row=2, column=0, pady=5, sticky=tk.W)
        self.cuda_var = tk.StringVar(value=self.cuda_versions[0] if self.cuda_versions else "12.1")
        cuda_combo = ttk.Combobox(main_frame, textvariable=self.cuda_var, values=self.cuda_versions)
        cuda_combo.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Build Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Build Options", padding="5")
        options_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        doc_text = (
            "These options are typically left unchecked for Windows builds.\n"
            "For details, see: https://www.deepspeed.ai/tutorials/advanced-install/\n"
            "Changing these may cause build failures on Windows systems."
        )
        
        # Documentation link
        doc_label = ttk.Label(
            options_frame,
            text=doc_text,
            foreground='dark red',
            justify=tk.LEFT,
            wraplength=800
        )
        doc_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Build options checkboxes
        self.build_options = {
            'DS_BUILD_AIO': tk.BooleanVar(value=False),
            'DS_BUILD_CUTLESS_OPS': tk.BooleanVar(value=False),
            'DS_BUILD_EVOFORMER_ATTN': tk.BooleanVar(value=False),
            'DS_BUILD_FP_QUANTIZER': tk.BooleanVar(value=False),
            'DS_BUILD_RAGGED_DEVICE_OPS': tk.BooleanVar(value=False),
            'DS_BUILD_SPARSE_ATTN': tk.BooleanVar(value=False),
            'DS_BUILD_INFERENCE_CORE_OPS': tk.BooleanVar(value=False)
        }
        
        # Create two columns of checkboxes
        for i, (option, var) in enumerate(self.build_options.items()):
            row = (i // 2) + 1  # Start after doc text
            col = i % 2
            ttk.Checkbutton(
                options_frame,
                text=option.replace('DS_BUILD_', ''),
                variable=var
            ).grid(row=row, column=col, padx=10, pady=2, sticky=tk.W)
        
        # Installation directory
        ttk.Label(main_frame, text="Installation Directory:", style='Header.TLabel').grid(row=4, column=0, pady=5, sticky=tk.W)
        self.install_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "deepspeed"))
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=4, column=1, pady=5, padx=5, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=self.install_dir_var, width=50).grid(row=0, column=0)
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(row=0, column=1, padx=5)
        
        # Admin rights warning
        warning_label = ttk.Label(
            main_frame, 
            text="Note: This tool requires administrative privileges to build DeepSpeed.",
            foreground='red'
        )
        warning_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Log area
        ttk.Label(main_frame, text="Installation Log:", style='Header.TLabel').grid(row=6, column=0, pady=5, sticky=tk.W)
        self.log_area = scrolledtext.ScrolledText(main_frame, height=20, width=100)
        self.log_area.grid(row=7, column=0, columnspan=2, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=8, column=0, columnspan=2, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        # Status label
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=9, column=0, columnspan=2, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=10)
        
        # Add CUDA Setup button alongside other buttons
        ttk.Button(button_frame, text="Build Only", style="Big.TButton", command=self.build_only).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Install Built Wheel", style="Big.TButton", command=self.install_wheel).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Build and Install", style="Big.TButton", command=self.start_installation).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="CUDA Setup Guide", style="Big.TButton", command=self.show_cuda_setup_info).grid(row=0, column=3, padx=5)        

        # Add separator and CUDA setup help text
        ttk.Separator(main_frame).grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")
        cuda_help = ttk.Label(
            main_frame,
            text="Note: Click 'CUDA Setup Guide' for instructions on setting up CUDA_HOME",
            foreground='dark blue'
        )
        cuda_help.grid(row=12, column=0, columnspan=2, pady=5)  


    def find_vs_installation(self):
        """Find Visual Studio installation with C++ build tools"""
        # First check default locations
        default_vs_paths = {
            "VS2019 BuildTools": "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools",
            "VS2019 Community": "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community",
            "VS2022 BuildTools": "C:\\Program Files\\Microsoft Visual Studio\\2022\\BuildTools",
            "VS2022 Community": "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community"
        }
        
        # Check default paths first
        for vs_name, vs_path in default_vs_paths.items():
            vcvars_path = os.path.join(vs_path, "VC\\Auxiliary\\Build\\vcvars64.bat")
            if os.path.exists(vcvars_path):
                return vs_name, vs_path, vcvars_path

        # If not found in default locations, check registry
        vs_reg_paths = [
            (r"SOFTWARE\Microsoft\VisualStudio\Setup\Community", "2022"),
            (r"SOFTWARE\Microsoft\VisualStudio\Setup\BuildTools", "2022"),
            (r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\Setup\Community", "2019"),
            (r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\Setup\BuildTools", "2019")
        ]
        
        for reg_path, version in vs_reg_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    install_path = winreg.QueryValueEx(key, "InstallDir")[0]
                    if install_path:
                        parent_path = str(Path(install_path).parent)
                        vcvars_path = os.path.join(parent_path, "VC", "Auxiliary", "Build", "vcvars64.bat")
                        if os.path.exists(vcvars_path):
                            edition = "Community" if "Community" in reg_path else "BuildTools"
                            vs_name = f"VS{version} {edition}"
                            return vs_name, parent_path, vcvars_path
            except WindowsError:
                continue
        
        return None, None, None
            
    def run_build_process(self):
        try:
            # Find VS installation using our detection method
            vs_name, vs_path, vcvars_path = self.find_vs_installation()
            
            if not vcvars_path:
                raise Exception("Visual Studio 64-bit build tools not found")
                
            self.log(f"Using Visual Studio 64-bit tools from: {vs_path}")

            # Create a batch file that will set up environment and run our build
            build_script = os.path.join(self.install_dir_var.get(), "run_build.bat")
            with open(build_script, 'w') as f:
                f.write('@echo off\n')
                f.write('chcp 65001\n')  # Set command window code page to UTF-8
                f.write('set PYTHONUTF8=1\n')  # Force Python to use UTF-8 for I/O
                f.write('set PYTHONIOENCODING=utf-8\n')  # Ensure Python uses UTF-8 for its I/O encoding                
                # Call vcvars64.bat explicitly for 64-bit environment
                f.write(f'call "{vcvars_path}"\n')
                #f.write(f'call "{vcvars_path}" x64 -vcvars_ver=14.29\n')
                # Skip Git hash
                f.write('set DS_BUILD_STRING=nogit\n')
                # Set up environment variables
                f.write(f'set CUDA_PATH=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}\n')
                f.write('set CUDA_HOME=%CUDA_PATH%\n')
                f.write('set DISTUTILS_USE_SDK=1\n')
                # Set DeepSpeed build options
                f.write('set DS_BUILD_AIO=0\n')
                f.write('set DS_BUILD_CUTLASS_OPS=0\n')
                f.write('set DS_BUILD_EVOFORMER_ATTN=0\n')
                f.write('set DS_BUILD_FP_QUANTIZER=0\n')
                f.write('set DS_BUILD_RAGGED_DEVICE_OPS=0\n')
                f.write('set DS_BUILD_SPARSE_ATTN=0\n')
                f.write('set DS_BUILD_TRANSFORMER_INFERENCE=0\n')
                # Echo environment for debugging
                f.write('echo ============ Environment Variables ============\n')
                f.write('echo CUDA_PATH=%CUDA_PATH%\n')
                f.write('echo CUDA_HOME=%CUDA_HOME%\n')
                f.write('echo PATH=%PATH%\n')
                f.write('echo INCLUDE=%INCLUDE%\n')
                f.write('echo Platform: %VSCMD_ARG_TGT_ARCH%\n')  # This will show if we're truly in 64-bit mode
                f.write('echo ============================================\n')
                # Change to build directory
                f.write(f'cd /d "{self.install_dir_var.get()}"\n')
                # Run the build command
                f.write(f'"{sys.executable}" setup.py bdist_wheel\n')
                f.write('if errorlevel 1 exit /b 1\n')

            # Run the build script
            self.log("Starting build with 64-bit tools...")
            process = subprocess.Popen(
                ['cmd', '/c', build_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log(output.strip())
                    self.root.update()

            if process.returncode != 0:
                raise Exception("Build failed")

            # Remove the temporary build script
            try:
                os.remove(build_script)
            except:
                pass

            return True

        except Exception as e:
            self.log(f"Build process error: {str(e)}")
            return False

    def manage_build_directory(self):
        """Manage build directory and wheel files"""
        try:
            # Create archive directory if it doesn't exist
            archive_dir = os.path.join(os.path.dirname(self.install_dir_var.get()), "deepspeed_wheels")
            os.makedirs(archive_dir, exist_ok=True)
            
            # Clear existing build directory if it exists
            if os.path.exists(self.install_dir_var.get()):
                self.log("Cleaning existing build directory...")
                shutil.rmtree(self.install_dir_var.get())
            
            # Create fresh build directory
            os.makedirs(self.install_dir_var.get())
            
            return True
        except Exception as e:
            self.log(f"Error managing build directory: {str(e)}")
            return False

    def archive_wheel(self):
        """Archive built wheel file with version info"""
        try:
            wheel_dir = os.path.join(self.install_dir_var.get(), 'dist')
            wheel_files = list(Path(wheel_dir).glob('*.whl'))
            if not wheel_files:
                return False
                
            # Create archive subdirectory with version info
            archive_subdir = f"deepspeed_{self.version_var.get()}_cuda{self.cuda_var.get()}_py{sys.version_info.major}{sys.version_info.minor}"
            archive_path = os.path.join(os.path.dirname(self.install_dir_var.get()), "deepspeed_wheels", archive_subdir)
            os.makedirs(archive_path, exist_ok=True)
            
            # Move wheel file
            shutil.copy2(str(wheel_files[0]), archive_path)
            self.log(f"Wheel file archived to: {archive_path}")
            
            return True
        except Exception as e:
            self.log(f"Error archiving wheel: {str(e)}")
            return False
        
    def build_only(self):
        """Only build the wheel without installing"""
        if not self.version_var.get():
            messagebox.showerror("Error", "Please select a DeepSpeed version")
            return

        try:
            # Show build environment info
            self.log("\nBuild Environment:")
            self.log(f"Python Version: {self.python_version}")
            self.log(f"PyTorch Version: {self.torch_version}")
            self.log(f"Selected CUDA Version: {self.cuda_var.get()}")
            self.log(f"Building DeepSpeed Version: {self.version_var.get()}\n")
            
            if not messagebox.askyesno("Confirm Build Environment", 
                                    f"Building DeepSpeed {self.version_var.get()} with:\n\n"
                                    f"Python: {self.python_version}\n"
                                    f"PyTorch: {self.torch_version}\n"
                                    f"CUDA: {self.cuda_var.get()}\n\n"
                                    "Continue?"):
                return
                
            self.progress_var.set(0)
            self.status_var.set("Starting build...")

            # Manage build directory BEFORE downloading
            if not self.manage_build_directory():
                raise Exception("Failed to prepare build directory")
            
            # Download and extract DeepSpeed
            version = self.version_var.get()
            self.log(f"Downloading DeepSpeed {version}...")
            
            url = f"https://github.com/microsoft/DeepSpeed/archive/v{version}.zip"
            self.log(f"Download URL: {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            zip_path = os.path.join(self.install_dir_var.get(), "deepspeed.zip")
            os.makedirs(self.install_dir_var.get(), exist_ok=True)
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.progress_var.set(30)
            
            # Extract
            self.log("Extracting files...")
            shutil.unpack_archive(zip_path, self.install_dir_var.get())
            extracted_dir = os.path.join(self.install_dir_var.get(), f"DeepSpeed-{version}")
            
            # Move contents up one level
            for item in os.listdir(extracted_dir):
                shutil.move(
                    os.path.join(extracted_dir, item),
                    os.path.join(self.install_dir_var.get(), item)
                )
            os.rmdir(extracted_dir)
            os.remove(zip_path)
            
            self.progress_var.set(50)
            
            # Run build
            if not self.run_build_process():
                raise Exception("Build failed")
            
            # Archive the wheel file after successful build
            if not self.archive_wheel():
                self.log("⚠ Warning: Could not archive wheel file")
            
            self.progress_var.set(100)
            self.status_var.set("Build complete!")
            self.log("✓ Build completed successfully!")
            # Show CUDA setup information
            if messagebox.askyesno("Build Success", 
                                "Build completed successfully! Would you like to view the CUDA_HOME setup instructions?"):
                self.show_cuda_setup_info()
            else:
                messagebox.showinfo("Success", "DeepSpeed has been successfully built!")
            
        except Exception as e:
            self.log(f"Error during build: {str(e)}")
            self.status_var.set("Build failed!")
            messagebox.showerror("Error", f"Build failed: {str(e)}")
            
    def install_wheel(self):
        """Install the previously built wheel"""
        try:
            self.log("Looking for built wheel...")
            wheel_dir = os.path.join(self.install_dir_var.get(), 'dist')
            wheel_files = list(Path(wheel_dir).glob('*.whl'))
            if not wheel_files:
                raise Exception("No wheel file found. Please build DeepSpeed first.")
            
            wheel_file = wheel_files[0]
            self.log(f"Found wheel: {wheel_file.name}")
            
            # First uninstall any existing DeepSpeed
            self.log("Uninstalling existing DeepSpeed...")
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'deepspeed', '-y'], 
                        check=False)  # Don't raise error if not installed
            
            # Install the wheel with dependencies
            self.log("Installing DeepSpeed wheel...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                str(wheel_file)
            ])
            
            self.log("✓ Installation completed successfully!")
            messagebox.showinfo("Success", "DeepSpeed has been successfully installed!")
            
        except Exception as e:
            self.log(f"Error during installation: {str(e)}")
            messagebox.showerror("Error", f"Installation failed: {str(e)}")

    def start_installation(self):
        """Build and install DeepSpeed"""
        if not self.version_var.get():
            messagebox.showerror("Error", "Please select a DeepSpeed version")
            return

        try:
            # Show build environment info
            self.log("\nBuild Environment:")
            self.log(f"Python Version: {self.python_version}")
            self.log(f"PyTorch Version: {self.torch_version}")
            self.log(f"Selected CUDA Version: {self.cuda_var.get()}")
            self.log(f"Building DeepSpeed Version: {self.version_var.get()}")
            
            if not messagebox.askyesno("Confirm Build Environment", 
                                    f"Building DeepSpeed {self.version_var.get()} with:\n\n"
                                    f"Python: {self.python_version}\n"
                                    f"PyTorch: {self.torch_version}\n"
                                    f"CUDA: {self.cuda_var.get()}\n\n"
                                    "Continue?"):
                return
                
            self.progress_var.set(0)
            self.status_var.set("Starting installation...")

            # Manage build directory BEFORE downloading
            if not self.manage_build_directory():
                raise Exception("Failed to prepare build directory")
            
            # Download DeepSpeed
            version = self.version_var.get()
            self.log(f"Downloading DeepSpeed {version}...")
            
            url = f"https://github.com/microsoft/DeepSpeed/archive/v{version}.zip"
            self.log(f"Download URL: {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            zip_path = os.path.join(self.install_dir_var.get(), "deepspeed.zip")
            os.makedirs(self.install_dir_var.get(), exist_ok=True)
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.progress_var.set(30)
            
            # Extract
            self.log("Extracting files...")
            shutil.unpack_archive(zip_path, self.install_dir_var.get())
            extracted_dir = os.path.join(self.install_dir_var.get(), f"DeepSpeed-{version}")
            
            # Move contents up one level
            for item in os.listdir(extracted_dir):
                shutil.move(
                    os.path.join(extracted_dir, item),
                    os.path.join(self.install_dir_var.get(), item)
                )
            os.rmdir(extracted_dir)
            os.remove(zip_path)
            
            self.progress_var.set(50)
            
            # Run build
            if not self.run_build_process():
                raise Exception("Build failed")
                
            # Archive the wheel file after successful build
            if not self.archive_wheel():
                self.log("⚠ Warning: Could not archive wheel file")
            
            self.progress_var.set(90)
            
            # Install wheel
            self.log("Installing wheel...")
            wheel_dir = os.path.join(self.install_dir_var.get(), 'dist')
            wheel_files = list(Path(wheel_dir).glob('*.whl'))
            if not wheel_files:
                raise Exception("No wheel file found after build")
            
            wheel_file = wheel_files[0]
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', str(wheel_file), '--force-reinstall'])
            
            self.progress_var.set(100)
            self.status_var.set("Installation complete!")
            self.log("✓ Installation completed successfully!")
            # Show CUDA setup information
            if messagebox.askyesno("Installation Success", 
                                "Installation completed successfully! Would you like to view the CUDA setup instructions?"):
                self.show_cuda_setup_info()
            else:
                messagebox.showinfo("Success", "DeepSpeed has been successfully installed!")
            
        except Exception as e:
            self.log(f"Error during installation: {str(e)}")
            self.status_var.set("Installation failed!")
            messagebox.showerror("Error", f"Installation failed: {str(e)}")

    def check_prerequisites(self):
        """Check all prerequisites"""
        self.progress_var.set(0)
        self.status_var.set("Checking prerequisites...")
        self.log("\nChecking prerequisites...")
        
        prerequisites_met = True
        
        # Check Visual Studio installation
        self.log("\nChecking Visual Studio installation:")
        vs_name, vs_path, vcvars_path = self.find_vs_installation()
        
        if vcvars_path:
            self.log(f"✓ Found {vs_name} at: {vs_path}")
            vs_found = True
        else:
            self.log("❌ No compatible Visual Studio installation found")
            self.log("Please install Visual Studio Community Edition from:")
            self.log("https://visualstudio.microsoft.com/vs/community/")
            self.log("During installation, select 'Desktop development with C++'")
            prerequisites_met = False
            vs_found = False
                   
        # Check CUDA installation
        self.log("\nChecking CUDA installation:")
        try:
            cuda_path = f"C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}"
            if not os.path.exists(cuda_path):
                self.log(f"❌ CUDA not found at: {cuda_path}")
                self.log("Please install CUDA Toolkit from:")
                self.log("https://developer.nvidia.com/cuda-toolkit-archive")
                self.log("Required components:")
                self.log("- CUDA > Development > Compiler > nvcc")
                self.log("- CUDA > Development > Libraries > CUBLAS")
                self.log("- CUDA > Runtime > Libraries > CUBLAS")
                prerequisites_met = False
            else:
                self.log(f"✓ Found CUDA installation at: {cuda_path}")
                
                # Check for nvcc
                nvcc_path = os.path.join(cuda_path, 'bin', 'nvcc.exe')
                if os.path.exists(nvcc_path):
                    self.log("✓ Found nvcc compiler")
                else:
                    self.log("❌ nvcc compiler not found - please install CUDA Development tools")
                    prerequisites_met = False
                
        except Exception as e:
            self.log(f"Error checking CUDA: {str(e)}")
            prerequisites_met = False
        
        # Check Python packages
        self.log("\nChecking Python packages:")
        try:
            required_packages = {
                'torch': "PyTorch is required for DeepSpeed",
                'ninja': "Ninja build system is required for compilation",
                'psutil': "psutil is required for system monitoring"
            }
            
            for package, description in required_packages.items():
                try:
                    if package == 'torch':
                        try:
                            import torch
                            self.log(f"✓ {package} {torch.__version__} is installed")
                            if torch.cuda.is_available():
                                self.log(f"  ✓ CUDA is available for PyTorch")
                                self.log(f"  ✓ CUDA Version: {torch.version.cuda}")
                            else:
                                self.log(f"  ⚠ CUDA is not available for PyTorch")
                        except ImportError:
                            self.log(f"❌ {package} is missing - {description}")
                            self.log("Please install PyTorch manually from: https://pytorch.org/get-started/locally/")
                            prerequisites_met = False
                    else:
                        try:
                            dist = distribution(package)
                            self.log(f"✓ {package} is installed")
                        except PackageNotFoundError:
                            self.log(f"! {package} is missing - attempting to install...")
                            try:
                                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                                self.log(f"✓ Successfully installed {package}")
                            except subprocess.CalledProcessError as e:
                                self.log(f"❌ Failed to install {package}: {str(e)}")
                                prerequisites_met = False
                except Exception as e:
                    self.log(f"❌ Error processing {package}: {str(e)}")
                    prerequisites_met = False
            
        except Exception as e:
            self.log(f"Error checking Python packages: {str(e)}")
            prerequisites_met = False
        
        # Final status update
        if prerequisites_met:
            self.log("\n✓ All prerequisites met!")
            self.status_var.set("Ready to install")
        else:
            self.log("\n❌ Some prerequisites are missing")
            self.log("Please install missing components before proceeding")
            self.status_var.set("Prerequisites check failed")
            messagebox.showerror("Prerequisites", 
                            "Some prerequisites are missing. Please check the log for details and installation instructions.")
        
        self.progress_var.set(100 if prerequisites_met else 0)
        return prerequisites_met

    def show_cuda_setup_info(self):
        """Show CUDA setup information"""
        cuda_info = f"""
        CUDA_HOME Setup Instructions for Windows 10/11
        =============================================
        DeepSpeed requires CUDA_HOME to be correctly set to function. This guide will help you set it up for your CUDA {self.cuda_var.get()} installation.

        Required CUDA_HOME path for your installation:
        CUDA_HOME = C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}

        Option 1: Set System-Wide (Python Environments can over-ride this setting)
        --------------------------------------------------------------------------
        1. Right-click on 'This PC' or 'Windows Start' → Click 'System'
        2. Click 'Advanced system settings' on the right
        3. Click 'Environment Variables' at the bottom
        4. Under 'System Variables', click 'New'
        5. Set as follows:
        Variable name:  CUDA_HOME
        Variable value: {os.path.join('C:', 'Program Files', 'NVIDIA GPU Computing Toolkit', 'CUDA', f'v{self.cuda_var.get()}')}
        6. Click 'OK' on all windows
        7. Restart any open Command Prompts or PowerShell windows

        Option 2: Set Temporarily (For testing or temporary use)
        --------------------------------------------------------
        Open Command Prompt and run:
        set CUDA_HOME=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}

        Note: This setting will be lost when you close the Command Prompt window.

        Option 3: Set in Conda Environment (For Conda users)
        ----------------------------------------------------
        1. Open Anaconda Prompt
        2. Run these commands:
        conda activate your_environment_name
        conda env config vars set CUDA_HOME=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}
        conda deactivate
        conda activate your_environment_name

        Option 4: Set in Virtual Environment (For venv users)
        -----------------------------------------------------
        1. Locate your venv's Scripts folder
        2. Edit 'activate.bat':
        Add this line at the end:
        set "CUDA_HOME=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}"

        3. Edit 'deactivate.bat':
        Add this line at the end:
        set "CUDA_HOME="

        Verification Steps
        ------------------
        1. Open a new Command Prompt
        2. Run: echo %CUDA_HOME%
        - Should show the CUDA path
        3. Run: %CUDA_HOME%\\bin\\nvcc -V
        - Should show CUDA version information

        Common Error Messages
        ---------------------
        1. "output = subprocess.check_output([cuda_home + "/bin/nvcc", "-V"], universal_newlines=True)"
           "FileNotFoundError: [WinError 2] The system cannot find the file specified"
           
        When running ds_report or using DeepSpeed, this typically means:
        - CUDA_HOME is not set
        - CUDA_HOME is set to the wrong path and it cannot access nvcc.exe from the CUDA Toolkit.
        - The CUDA installation is incomplete
        
         Verify that:
        - A CUDA Toolkit is properly installed
        - The correct CUDA_HOME path is set to the correct path
        - CUDA\\v{self.cuda_var.get()}\\bin exists and contains nvcc.exe

        Need Help?
        ---------
        - Verify CUDA installation at: C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v{self.cuda_var.get()}
        - Check that all required CUDA components are installed
        - Make sure to restart any command windows after setting CUDA_HOME
        - When using IDEs (PyCharm, VSCode, etc.), restart them after setting CUDA_HOME
        """
        # Show in log
        self.log(cuda_info)
        
        # Also show in separate window for easy copying
        info_window = tk.Toplevel(self.root)
        info_window.title("CUDA Setup Instructions")
        info_window.geometry("1200x1200")
        
        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
        text_widget.pack(expand=True, fill='both', padx=10, pady=10)
        text_widget.insert(tk.END, cuda_info)
        text_widget.configure(state='disabled')  # Make read-only

        # Add copy button
        def copy_text():
            info_window.clipboard_clear()
            info_window.clipboard_append(cuda_info)
            messagebox.showinfo("Copied", "Instructions copied to clipboard!")
        
        copy_button = ttk.Button(info_window, text="Copy to Clipboard", command=copy_text)
        copy_button.pack(pady=5)

    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        finally:
            # Close log file when application exits
            if hasattr(self, 'log_file'):
                self.log_file.close()            
            
def main():
    app = DeepSpeedPatcher()
    app.run()

if __name__ == "__main__":
    main()
