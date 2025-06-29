#!/usr/bin/env python3
"""
sync_spec.py - Synchronize buildozer.spec with project configuration

This script updates buildozer.spec to match current project settings:
- Package name and metadata from pyproject.toml
- Requirements and dependency management
- Platform-specific configurations
"""

import re
from pathlib import Path
import tomllib


def load_project_config():
    """Load configuration from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    return config


def update_buildozer_spec():
    """Update buildozer.spec with current project configuration"""
    config = load_project_config()
    project = config["project"]
    
    spec_path = Path(__file__).parent.parent / "buildozer.spec"
    
    # Read current spec
    with open(spec_path, "r") as f:
        spec_content = f.read()
    
    # Define updates based on pyproject.toml
    updates = {
        # Package identification
        "title": "KivyMD Chat UI",
        "package.name": "KivyChatUI", 
        "package.domain": "com.kivymd.chatui",
        
        # Version from pyproject.toml
        "version": project["version"],
        
        # Requirements - core dependencies only (no optional deps for Android build)
        "requirements": ",".join([
            "python3",
            "kivy==2.3.1", 
            "https://github.com/kivymd/KivyMD/archive/master.zip",
            "websockets==13.1",
            "setuptools>=80.9.0",
            "filetype",
            "materialyoucolor",
            "asynckivy",
            "asyncgui",
            # Note: pyjnius will be added by p4a automatically when needed
        ]),
        
        # Android permissions for chat app with STT
        "android.permissions": "INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,RECORD_AUDIO",
        
        # Target modern Android versions
        "android.api": "34",
        "android.minapi": "26", 
        "android.sdk": "34",
        "android.ndk": "25b",
        "android.ndk_api": "26",
        
        # Exclude development and build artifacts
        "source.exclude_dirs": "tests,bin,venv,.git,__pycache__,.pytest_cache,.venv,artefacts,scripts",
        
        # Include our Java classes for STT
        "android.add_src": "java",
    }
    
    # Apply updates
    for key, value in updates.items():
        pattern = rf"^{re.escape(key)}\s*=.*$"
        replacement = f"{key} = {value}"
        spec_content = re.sub(pattern, replacement, spec_content, flags=re.MULTILINE)
    
    # Write updated spec
    with open(spec_path, "w") as f:
        f.write(spec_content)
    
    print("✅ buildozer.spec updated successfully!")
    print("\nKey updates:")
    for key, value in updates.items():
        print(f"  {key} = {value}")


if __name__ == "__main__":
    update_buildozer_spec() 