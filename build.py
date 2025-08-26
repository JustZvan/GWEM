from cx_Freeze import setup

# Dependencies are automatically detected, but they might need fine-tuning.
build_exe_options = {
    "excludes": ["tkinter", "unittest"],
    "zip_include_packages": ["PySide6"],
    "include_files": ["assets/"],
}

setup(
    name="GWEM",
    version="0.1",
    description="My GUI application!",
    options={"build_exe": build_exe_options},
    executables=[{"script": "main.py", "base": "gui", "icon": "assets/icon.ico"}],
)
