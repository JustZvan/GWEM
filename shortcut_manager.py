import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import winshell


class ShortcutManager:

    def __init__(self):
        self.start_menu_path = (
            Path(os.environ.get("APPDATA", ""))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )
        self.shortcuts_dir = self.start_menu_path / "GWEM"
        self._ensure_shortcuts_directory()

    def _ensure_shortcuts_directory(self):
        self.shortcuts_dir.mkdir(parents=True, exist_ok=True)

    def _get_app_executable_path(
        self, app_name: str, executable_name: str, executable_subpath: str = ""
    ) -> Optional[Path]:
        try:
            apps_file = Path(os.environ.get("APPDATA", "")) / "GWEM" / "apps.json"

            if not apps_file.exists():
                print(f"GWEM apps.json not found at {apps_file}")
                return None

            with open(apps_file, "r", encoding="utf-8") as f:
                apps_data = json.load(f)

            if app_name not in apps_data:
                print(f"App '{app_name}' not found in apps.json")
                return None

            app_info = apps_data[app_name]

            if not app_info.get("installed", False):
                print(f"App '{app_name}' is not marked as installed")
                return None

            active_version = app_info.get("active_version")
            if not active_version:
                print(f"App '{app_name}' has no active version set")
                return None

            installed_versions = app_info.get("installed_versions", {})
            if active_version not in installed_versions:
                print(
                    f"Active version '{active_version}' not found in installed versions for '{app_name}'"
                )
                return None

            install_path = Path(installed_versions[active_version])
            if not install_path.exists():
                print(f"Install path does not exist: {install_path}")
                return None

            executable_path = install_path
            if executable_subpath:
                executable_path = executable_path / executable_subpath
            executable_path = executable_path / executable_name

            if executable_path.exists():
                return executable_path
            else:
                print(f"Executable not found: {executable_path}")
                return None

        except Exception as e:
            print(f"Error getting executable path for {app_name}: {e}")
            return None

    def create_shortcut(
        self,
        app_name: str,
        executable_name: str,
        shortcut_name: str = None,
        executable_subpath: str = "",
        description: str = "",
        icon_path: str = "",
        working_directory: str = "",
        arguments: str = "",
    ) -> Optional[Path]:
        if shortcut_name is None:
            shortcut_name = app_name

        shortcut_path = self.shortcuts_dir / f"{shortcut_name}.lnk"

        script_path = self._create_launcher_script(
            app_name, executable_name, executable_subpath, shortcut_name
        )
        if not script_path:
            print(f"Failed to create launcher script for {app_name}")
            return None

        try:
            if not icon_path:
                current_executable = self._get_app_executable_path(
                    app_name, executable_name, executable_subpath
                )
                if current_executable:
                    icon_path = str(current_executable)
                else:
                    icon_path = (
                        "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                    )

            if not description:
                description = f"{app_name} - Managed by GWEM"

            if not working_directory:
                working_directory = str(self.shortcuts_dir)

            winshell.CreateShortcut(
                Path=str(shortcut_path),
                Target="C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                Icon=(icon_path, 0),
                Description=description,
                StartIn=working_directory,
                Arguments=f'-WindowStyle Hidden -ExecutionPolicy Bypass -File "{script_path}" {arguments}'.strip(),
            )

            print(f"Created shortcut: {shortcut_path}")
            return shortcut_path

        except Exception as e:
            print(f"Error creating shortcut for {app_name}: {e}")
            return None

    def _create_launcher_script(
        self,
        app_name: str,
        executable_name: str,
        executable_subpath: str = "",
        shortcut_name: str = None,
    ) -> Optional[Path]:
        if shortcut_name is None:
            shortcut_name = app_name

        script_path = self.shortcuts_dir / f"{shortcut_name}_launcher.ps1"

        script_content = f"""# Auto-generated launcher script for {executable_name} ({app_name})
# This script dynamically resolves to the active version

param([Parameter(ValueFromRemainingArguments=$true)]$Args)

try {{
    # Get the GWEM appdata directory
    $gwemDir = Join-Path $env:APPDATA "GWEM"
    $appsJsonPath = Join-Path $gwemDir "apps.json"
    
    if (-not (Test-Path $appsJsonPath)) {{
        Write-Host "GWEM apps.json not found at $appsJsonPath" -ForegroundColor Red
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    # Read and parse apps.json
    $appsData = Get-Content $appsJsonPath | ConvertFrom-Json
    
    if (-not $appsData.PSObject.Properties.Name -contains "{app_name}") {{
        Write-Host "{app_name} is not installed or not found in apps.json" -ForegroundColor Red
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    $appInfo = $appsData."{app_name}"
    
    if (-not $appInfo.installed) {{
        Write-Host "{app_name} is installed but marked as not active" -ForegroundColor Red
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    # Get the active version and its install path
    $activeVersion = $appInfo.active_version
    if (-not $activeVersion) {{
        Write-Host "{app_name} has no active version set" -ForegroundColor Red
        Write-Host "Available versions: $($appInfo.installed_versions | ConvertTo-Json)" -ForegroundColor Yellow
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    Write-Host "Active version for {app_name}: $activeVersion" -ForegroundColor Green
    
    $installedVersions = $appInfo.installed_versions
    if (-not $installedVersions -or -not $installedVersions.PSObject.Properties.Name -contains $activeVersion) {{
        Write-Host "{app_name} active version $activeVersion not found in installed versions" -ForegroundColor Red
        Write-Host "Available versions: $($installedVersions | ConvertTo-Json)" -ForegroundColor Yellow
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    $installPath = $installedVersions.$activeVersion
    if (-not $installPath) {{
        Write-Host "{app_name} install path not found for active version $activeVersion" -ForegroundColor Red
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    Write-Host "Install path: $installPath" -ForegroundColor Green
    
    # Construct the path to the executable
    $executablePath = $installPath"""

        # Add subdirectory path if specified
        if executable_subpath:
            script_content += f'''
    $executablePath = Join-Path $executablePath "{executable_subpath}"'''

        script_content += f"""
    
    # Dynamically find the executable instead of using hardcoded name
    $foundExecutable = $null
    $searchPattern = "{executable_name.split('_')[0].lower()}*"  # Use the base name (e.g., "godot*")
    
    Write-Host "Searching for executable matching pattern: $searchPattern" -ForegroundColor Green
    Write-Host "In directory: $executablePath" -ForegroundColor Green
    
    if (Test-Path $executablePath) {{
        $candidates = Get-ChildItem $executablePath -Filter "*.exe" | Where-Object {{ 
            $_.Name.ToLower().StartsWith("{executable_name.split('_')[0].lower()}") 
        }}
        
        if ($candidates.Count -gt 0) {{
            $foundExecutable = $candidates[0].FullName
            Write-Host "Found executable: $foundExecutable" -ForegroundColor Green
        }} else {{
            Write-Host "No executable found matching pattern $searchPattern" -ForegroundColor Red
            Write-Host "Directory contents:" -ForegroundColor Yellow
            Get-ChildItem $executablePath | ForEach-Object {{ Write-Host "  $($_.Name)" -ForegroundColor Yellow }}
            Read-Host "Press Enter to continue..."
            exit 1
        }}
    }} else {{
        Write-Host "Directory not found: $executablePath" -ForegroundColor Red
        Read-Host "Press Enter to continue..."
        exit 1
    }}
    
    Write-Host "Launching: $foundExecutable" -ForegroundColor Green
    Write-Host "Arguments: $Args" -ForegroundColor Green
    
    # Execute the actual program with all passed arguments
    if ($Args.Count -eq 0) {{
        & $foundExecutable
    }} else {{
        & $foundExecutable @Args
    }}
    
    # Forward the exit code
    exit $LASTEXITCODE
    
}} catch {{
    Write-Host "Error in {executable_name} launcher: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
    Read-Host "Press Enter to continue..."
    exit 1
}}
"""

        try:
            # Write the launcher script
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            print(f"Created launcher script: {script_path}")
            return script_path
        except Exception as e:
            print(f"Error creating launcher script for {app_name}: {e}")
            return None

    def create_multiple_shortcuts(
        self, app_name: str, shortcuts_config: List[Dict[str, str]]
    ) -> List[Path]:
        created_shortcuts = []
        for config in shortcuts_config:
            executable_name = config["executable_name"]
            shortcut_name = config.get("shortcut_name", None)
            executable_subpath = config.get("executable_subpath", "")
            description = config.get("description", "")
            icon_path = config.get("icon_path", "")
            working_directory = config.get("working_directory", "")
            arguments = config.get("arguments", "")

            shortcut_path = self.create_shortcut(
                app_name=app_name,
                executable_name=executable_name,
                shortcut_name=shortcut_name,
                executable_subpath=executable_subpath,
                description=description,
                icon_path=icon_path,
                working_directory=working_directory,
                arguments=arguments,
            )

            if shortcut_path:
                created_shortcuts.append(shortcut_path)

        return created_shortcuts

    def remove_shortcut(self, shortcut_name: str) -> bool:
        shortcut_path = self.shortcuts_dir / f"{shortcut_name}.lnk"
        script_path = self.shortcuts_dir / f"{shortcut_name}_launcher.ps1"

        removed = False

        # ...existing code...
        if shortcut_path.exists():
            try:
                shortcut_path.unlink()
                print(f"Removed shortcut: {shortcut_path}")
                removed = True
            except Exception as e:
                print(f"Error removing shortcut {shortcut_path}: {e}")

        # ...existing code...
        if script_path.exists():
            try:
                script_path.unlink()
                print(f"Removed launcher script: {script_path}")
            except Exception as e:
                print(f"Error removing launcher script {script_path}: {e}")

        if not shortcut_path.exists() and not removed:
            print(f"Shortcut not found: {shortcut_path}")
            return False

        return removed

    def remove_multiple_shortcuts(self, shortcut_names: List[str]) -> int:
        removed_count = 0
        for shortcut_name in shortcut_names:
            if self.remove_shortcut(shortcut_name):
                removed_count += 1
        return removed_count

    def list_shortcuts(self) -> List[Path]:
        if not self.shortcuts_dir.exists():
            return []
        return list(self.shortcuts_dir.glob("*.lnk"))

    def get_shortcuts_directory(self) -> Path:
        return self.shortcuts_dir

    def is_shortcut_exists(self, shortcut_name: str) -> bool:
        shortcut_path = self.shortcuts_dir / f"{shortcut_name}.lnk"
        return shortcut_path.exists()

    def update_shortcut(
        self,
        app_name: str,
        executable_name: str,
        shortcut_name: str = None,
        executable_subpath: str = "",
        description: str = "",
        icon_path: str = "",
        working_directory: str = "",
        arguments: str = "",
    ) -> Optional[Path]:
        if shortcut_name is None:
            shortcut_name = app_name

        if self.is_shortcut_exists(shortcut_name):
            self.remove_shortcut(shortcut_name)

        return self.create_shortcut(
            app_name=app_name,
            executable_name=executable_name,
            shortcut_name=shortcut_name,
            executable_subpath=executable_subpath,
            description=description,
            icon_path=icon_path,
            working_directory=working_directory,
            arguments=arguments,
        )

    def cleanup_app_shortcuts(self, app_name: str) -> int:
        removed_count = 0

        # Remove .lnk files
        shortcuts = self.list_shortcuts()
        for shortcut_path in shortcuts:
            shortcut_name = shortcut_path.stem
            if shortcut_name.lower().startswith(app_name.lower()):
                try:
                    shortcut_path.unlink()
                    print(f"Removed shortcut: {shortcut_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing shortcut {shortcut_path}: {e}")

        # Remove launcher scripts
        if self.shortcuts_dir.exists():
            launcher_scripts = list(self.shortcuts_dir.glob("*_launcher.ps1"))
            for script_path in launcher_scripts:
                script_name = script_path.stem.replace("_launcher", "")
                if script_name.lower().startswith(app_name.lower()):
                    try:
                        script_path.unlink()
                        print(f"Removed launcher script: {script_path}")
                    except Exception as e:
                        print(f"Error removing launcher script {script_path}: {e}")

        return removed_count


shortcut_manager = ShortcutManager()
