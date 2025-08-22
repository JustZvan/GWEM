"""
i will be honest, this one was made by chatgpt because no way im writing powershell

thanks for understand
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from state_manager import PATH_DIR, state_manager


class ShimManager:
    """Manages creation and removal of PowerShell shims for applications"""

    def __init__(self):
        self.shims_dir = PATH_DIR
        self._ensure_shims_directory()

    def _ensure_shims_directory(self):
        """Ensure the shims directory exists"""
        self.shims_dir.mkdir(parents=True, exist_ok=True)

    def create_shim(
        self, app_name: str, executable_name: str, executable_subpath: str = ""
    ):
        """
        Create a PowerShell shim for an executable

        Args:
            app_name: Name of the app in apps.json (e.g., 'nodejs')
            executable_name: Name of the executable (e.g., 'node', 'npm')
            executable_subpath: Subdirectory path within the app install directory to the executable
                               (e.g., 'bin' or 'node-v20.0.0-win-x64')
        """
        shim_path = self.shims_dir / f"{executable_name}.ps1"

        # PowerShell script content that reads apps.json and launches the latest version
        script_content = f"""# Auto-generated shim for {executable_name} ({app_name})
# This script dynamically resolves to the latest installed version

param([Parameter(ValueFromRemainingArguments=$true)]$Args)

try {{
    # Get the GWEM appdata directory
    $gwemDir = Join-Path $env:APPDATA "GWEM"
    $appsJsonPath = Join-Path $gwemDir "apps.json"
    
    if (-not (Test-Path $appsJsonPath)) {{
        Write-Error "GWEM apps.json not found at $appsJsonPath"
        exit 1
    }}
    
    # Read and parse apps.json
    $appsData = Get-Content $appsJsonPath | ConvertFrom-Json
    
    if (-not $appsData.PSObject.Properties.Name -contains "{app_name}") {{
        Write-Error "{app_name} is not installed or not found in apps.json"
        exit 1
    }}
    
    $appInfo = $appsData."{app_name}"
    
    if (-not $appInfo.installed) {{
        Write-Error "{app_name} is installed but marked as not active"
        exit 1
    }}
    
    # Get the active version and its install path
    $activeVersion = $appInfo.active_version
    if (-not $activeVersion) {{
        Write-Error "{app_name} has no active version set"
        exit 1
    }}
    
    $installedVersions = $appInfo.installed_versions
    if (-not $installedVersions -or -not $installedVersions.PSObject.Properties.Name -contains $activeVersion) {{
        Write-Error "{app_name} active version $activeVersion not found in installed versions"
        exit 1
    }}
    
    $installPath = $installedVersions.$activeVersion
    if (-not $installPath) {{
        Write-Error "{app_name} install path not found for active version $activeVersion"
        exit 1
    }}
    
    # Construct the path to the executable
    $executablePath = $installPath"""

        # Add subdirectory path if specified
        if executable_subpath:
            script_content += f'''
    $executablePath = Join-Path $executablePath "{executable_subpath}"'''

        script_content += f"""
    $executablePath = Join-Path $executablePath "{executable_name}.exe"
    
    if (-not (Test-Path $executablePath)) {{
        Write-Error "Executable not found at $executablePath"
        exit 1
    }}
    
    # Execute the actual program with all passed arguments
    if ($Args.Count -eq 0) {{
        & $executablePath
    }} else {{
        & $executablePath @Args
    }}
    
    # Forward the exit code
    exit $LASTEXITCODE
    
}} catch {{
    Write-Error "Error in {executable_name} shim: $($_.Exception.Message)"
    exit 1
}}
"""

        # Write the shim script
        with open(shim_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        print(f"Created shim: {shim_path}")
        return shim_path

    def create_multiple_shims(self, app_name: str, shims_config: List[Dict[str, str]]):
        """
        Create multiple shims for an application

        Args:
            app_name: Name of the app in apps.json
            shims_config: List of dictionaries with 'executable_name' and optional 'executable_subpath'
        """
        created_shims = []
        for config in shims_config:
            executable_name = config["executable_name"]
            executable_subpath = config.get("executable_subpath", "")
            shim_path = self.create_shim(app_name, executable_name, executable_subpath)
            created_shims.append(shim_path)
        return created_shims

    def remove_shim(self, executable_name: str):
        """Remove a shim file"""
        shim_path = self.shims_dir / f"{executable_name}.ps1"
        if shim_path.exists():
            shim_path.unlink()
            print(f"Removed shim: {shim_path}")
            return True
        else:
            print(f"Shim not found: {shim_path}")
            return False

    def remove_multiple_shims(self, executable_names: List[str]):
        """Remove multiple shim files"""
        removed_count = 0
        for executable_name in executable_names:
            if self.remove_shim(executable_name):
                removed_count += 1
        return removed_count

    def list_shims(self) -> List[Path]:
        """List all existing shim files"""
        if not self.shims_dir.exists():
            return []
        return list(self.shims_dir.glob("*.ps1"))

    def get_shims_directory(self) -> Path:
        """Get the shims directory path"""
        return self.shims_dir

    def is_shim_exists(self, executable_name: str) -> bool:
        """Check if a shim exists for the given executable"""
        shim_path = self.shims_dir / f"{executable_name}.ps1"
        return shim_path.exists()


# Global shim manager instance
shim_manager = ShimManager()
