"""
Platform-specific utilities for Windows Registry and macOS plist operations.
This module provides a unified interface for common operations across platforms.
"""

import os
import sys
import logging
import subprocess

_LOGGER = logging.getLogger(__name__)

# Import platform-specific modules
if sys.platform == "win32":
    import winreg
elif sys.platform == "darwin":
    import plistlib
    import subprocess

# Constants
WINDOWS_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RMLAPP_KEY_PATH = r"SOFTWARE\Rainbow Music Led\RmlApp"
MACOS_PLIST_PATH = "~/Library/Preferences/com.rainbow-music-led.RmlApp.plist"
MACOS_PLIST_DOMAIN = "com.rainbow-music-led.RmlApp"
MACOS_LAUNCH_AGENTS_DIR = "~/Library/LaunchAgents"

# Application names in registry/plist
WLS_APP_NAME = "A-WiFi Led Studio"
RMLAPP_NAME = "A-Rainbow Music Led"

# Launch agent file names
WLS_LAUNCH_AGENT = "com.wls.startup.plist"
RMLAPP_LAUNCH_AGENT = "com.rmlapp.startup.plist"

if sys.platform == "win32":
    class RegistryManager:
        """Handles Windows registry operations."""

        @staticmethod
        def open_or_create_key(key_path, access=winreg.KEY_ALL_ACCESS):
            """Open a registry key, creating it if it doesn't exist."""
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, access)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            return key

        @staticmethod
        def set_value(key_path, value_name, value_data, value_type=winreg.REG_SZ):
            """Set a registry value, creating the key if needed."""
            try:
                key = RegistryManager.open_or_create_key(key_path)
                winreg.SetValueEx(key, value_name, 0, value_type, value_data)
                winreg.CloseKey(key)
                return True
            except Exception as e:
                _LOGGER.error(f"Error setting registry value {value_name}: {e}")
                return False

        @staticmethod
        def delete_value(key_path, value_name):
            """Delete a registry value if it exists."""
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.DeleteValue(key, value_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                # Key or value doesn't exist, which is fine
                return True
            except Exception as e:
                _LOGGER.error(f"Error deleting registry value {value_name}: {e}")
                return False

        @staticmethod
        def get_value(key_path, value_name, default=None):
            """Get a registry value, returning default if it doesn't exist."""
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                return value
            except (FileNotFoundError, WindowsError):
                return default

        @staticmethod
        def check_value_exists(key_path, value_name):
            """Check if a registry value exists."""
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                return True
            except (FileNotFoundError, WindowsError):
                return False

        @staticmethod
        def enumerate_values(key_path):
            """Enumerate all values in a registry key."""
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                count = winreg.QueryInfoKey(key)[1]
                result = []

                for i in range(count):
                    value_name, value_data, value_type = winreg.EnumValue(key, i)
                    result.append((value_name, value_data, value_type))

                winreg.CloseKey(key)
                return result
            except FileNotFoundError:
                return []
            except Exception as e:
                _LOGGER.error(f"Error enumerating registry values: {e}")
                return []
elif sys.platform == "darwin":
    class PlistManager:
        """Handles macOS plist operations."""

        @staticmethod
        def _expand_path(path):
            """Expand user path if needed."""
            return os.path.expanduser(path) if '~' in path else path

        @staticmethod
        def set_value(domain, key, value, use_defaults=True):
            """Set a value in a plist file."""
            try:
                if use_defaults:
                    # Try using defaults command first (preferred method)
                    # Determine the correct type flag based on the value type
                    if isinstance(value, bool):
                        value_type = "-bool"
                        value_str = str(value).lower()
                    elif isinstance(value, int):
                        value_type = "-int"
                        value_str = str(value)
                    elif isinstance(value, float):
                        value_type = "-float"
                        value_str = str(value)
                    else:
                        value_type = "-string"
                        value_str = str(value)

                    subprocess.run([
                        'defaults', 'write',
                        domain, key, value_type, value_str
                    ], check=True)
                    return True
                else:
                    # Fallback to plistlib
                    plist_path = PlistManager._expand_path(MACOS_PLIST_PATH)

                    # Read existing plist if it exists
                    if os.path.exists(plist_path):
                        with open(plist_path, 'rb') as fp:
                            plist_data = plistlib.load(fp)
                    else:
                        plist_data = {}

                    # Update value
                    plist_data[key] = value

                    # Write back to file
                    with open(plist_path, 'wb') as fp:
                        plistlib.dump(plist_data, fp, fmt=plistlib.FMT_XML)

                    return True
            except Exception as e:
                _LOGGER.error(f"Error setting plist value {key}: {e}")
                return False

        @staticmethod
        def get_value(domain, key, default=None):
            """Get a value from a plist file."""
            try:
                # Try using defaults command first
                result = subprocess.run([
                    'defaults', 'read',
                    domain, key
                ], capture_output=True, text=True, check=False)

                if result.returncode == 0:
                    value = result.stdout.strip()
                    # Convert "1" and "0" to boolean if they appear to be boolean values
                    if value == "1":
                        return True
                    elif value == "0":
                        return False

                    # Try to convert to integer if it looks like an integer
                    try:
                        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                            return int(value)
                    except (ValueError, AttributeError):
                        pass

                    # Try to convert to float if it looks like a float
                    try:
                        if '.' in value:
                            return float(value)
                    except (ValueError, AttributeError):
                        pass

                    return value

                # Fallback to plistlib
                plist_path = PlistManager._expand_path(MACOS_PLIST_PATH)
                if os.path.exists(plist_path):
                    with open(plist_path, 'rb') as fp:
                        plist_data = plistlib.load(fp)
                    return plist_data.get(key, default)

                return default
            except Exception as e:
                _LOGGER.error(f"Error getting plist value {key}: {e}")
                return default

        @staticmethod
        def delete_value(domain, key):
            """Delete a value from a plist file."""
            try:
                # Try using defaults command first
                subprocess.run([
                    'defaults', 'delete',
                    domain, key
                ], check=False)  # Don't check result as it might not exist

                return True
            except Exception as e:
                _LOGGER.error(f"Error deleting plist value {key}: {e}")
                return False

        @staticmethod
        def copy_launch_agent(source_path, agent_name):
            """Copy a launch agent plist file to the LaunchAgents directory."""
            try:
                destination = os.path.join(
                    PlistManager._expand_path(MACOS_LAUNCH_AGENTS_DIR),
                    agent_name
                )
                shutil.copy(source_path, destination)
                return True
            except Exception as e:
                _LOGGER.error(f"Error copying launch agent {agent_name}: {e}")
                return False

        @staticmethod
        def remove_launch_agent(agent_name):
            """Remove a launch agent plist file from the LaunchAgents directory."""
            try:
                path = os.path.join(
                    PlistManager._expand_path(MACOS_LAUNCH_AGENTS_DIR),
                    agent_name
                )
                if os.path.exists(path):
                    os.remove(path)
                return True
            except Exception as e:
                _LOGGER.error(f"Error removing launch agent {agent_name}: {e}")
                return False

        @staticmethod
        def check_launch_agent_exists(agent_name):
            """Check if a launch agent plist file exists."""
            path = os.path.join(
                PlistManager._expand_path(MACOS_LAUNCH_AGENTS_DIR),
                agent_name
            )
            return os.path.isfile(path)

# Platform-agnostic functions

def set_device_enabled(device_id, enabled):
    """Set the enabled state for a device across platforms.
    
    Args:
        device_id: Device ID or None for global/systray state
        enabled: Boolean indicating whether the device is enabled
    """
    value = "true" if enabled else "false"
    bool_value = True if enabled else False

    if sys.platform == "win32":
        # Windows registry
        if device_id is None:
            # Global/systray state
            systray_reg_path = f"{WINDOWS_RMLAPP_KEY_PATH}\\SystrayState"
            result = RegistryManager.set_value(systray_reg_path, "deviceEnabled", value)
            if result:
                _LOGGER.debug(f"Updated registry with SystrayState.deviceEnabled={value}")
            return result
        else:
            # Device-specific state
            device_reg_path = f"{WINDOWS_RMLAPP_KEY_PATH}\\Instance_{device_id}"
            result = RegistryManager.set_value(device_reg_path, "deviceEnabled", value)
            if result:
                _LOGGER.debug(f"Updated registry with deviceEnabled={value} for device {device_id}")
            return result

    elif sys.platform == "darwin":
        # macOS plist
        if device_id is None:
            # Global/systray state
            key_name = "SystrayState.deviceEnabled"
        else:
            # Device-specific state
            key_name = f"Instance_{device_id}.deviceEnabled"

        # Try defaults command first, fall back to plistlib if it fails
        try:
            result = PlistManager.set_value(MACOS_PLIST_DOMAIN, key_name, bool_value)
            if result:
                if device_id is None:
                    _LOGGER.debug(f"Updated plist with SystrayState.deviceEnabled={bool_value}")
                else:
                    _LOGGER.debug(f"Updated plist with deviceEnabled={bool_value} for device {device_id}")
            return result
        except Exception as e:
            _LOGGER.error(f"Error updating device enabled state: {e}")
            return False

    return False

def set_device_brightness(device_id, brightness_value):
    """Set the brightness for a device across platforms.
    
    Args:
        device_id: Device ID or None for global/systray brightness
        brightness_value: Float between 0.0 and 1.0
    """
    # Convert to integer percentage (0-100)
    brightness_int = int(brightness_value * 100)

    if sys.platform == "win32":
        # Windows registry
        reg_path = WINDOWS_RMLAPP_KEY_PATH

        if device_id is None:
            # Global/systray brightness
            systray_reg_path = f"{reg_path}\\SystrayState"
            result = RegistryManager.set_value(systray_reg_path, "brightness", brightness_int, winreg.REG_DWORD)
        else:
            # Device-specific brightness
            device_reg_path = f"{reg_path}\\Instance_{device_id}"
            result = RegistryManager.set_value(device_reg_path, "brightness", brightness_int, winreg.REG_DWORD)

        if result:
            _LOGGER.debug(f"Updated registry with brightness={brightness_int}% for {'device '+str(device_id) if device_id else 'all devices'}")
        return result

    elif sys.platform == "darwin":
        # macOS plist
        key_name = f"Instance_{device_id}.brightness" if device_id else "SystrayState.brightness"

        try:
            # For brightness, we use the integer value directly
            result = PlistManager.set_value(MACOS_PLIST_DOMAIN, key_name, brightness_int)
            if result:
                _LOGGER.debug(f"Updated plist with brightness={brightness_int}% for {'device '+str(device_id) if device_id else 'all devices'}")
            return result
        except Exception as e:
            _LOGGER.error(f"Error updating device brightness: {e}")
            return False

    return False

def set_selected_device(device_id=None):
    """Set the selected device in registry/plist.
    
    Args:
        device_id: Device ID or None for all devices
    """
    if sys.platform == "win32":
        # Windows registry
        try:
            if device_id is None:
                # Set to all devices (0xFFFFFFFF or -1)
                try:
                    # Try with 0xFFFFFFFF (unsigned 32-bit max value)
                    result = RegistryManager.set_value(WINDOWS_RMLAPP_KEY_PATH, "selectedInstance", 0xFFFFFFFF & 0xFFFFFFFF, winreg.REG_DWORD)
                    if result:
                        _LOGGER.debug("Updated registry with selectedInstance: 0xFFFFFFFF (all devices)")
                        return True
                except Exception:
                    # Try with -1
                    try:
                        result = RegistryManager.set_value(WINDOWS_RMLAPP_KEY_PATH, "selectedInstance", -1, winreg.REG_DWORD)
                        if result:
                            _LOGGER.debug("Updated registry with selectedInstance: -1 (all devices)")
                            return True
                    except Exception:
                        # Last resort: use a string value
                        result = RegistryManager.set_value(WINDOWS_RMLAPP_KEY_PATH, "selectedInstance", "-1", winreg.REG_SZ)
                        if result:
                            _LOGGER.debug("Updated registry with selectedInstance: '-1' (string, all devices)")
                            return True
            else:
                # Set to specific device
                try:
                    # Try to convert to integer
                    dev_id_int = int(device_id)
                    result = RegistryManager.set_value(WINDOWS_RMLAPP_KEY_PATH, "selectedInstance", dev_id_int, winreg.REG_DWORD)
                    if result:
                        _LOGGER.debug(f"Updated registry with selectedInstance: {dev_id_int}")
                        return True
                except (ValueError, TypeError):
                    # If conversion fails, use 0 as default
                    result = RegistryManager.set_value(WINDOWS_RMLAPP_KEY_PATH, "selectedInstance", 0, winreg.REG_DWORD)
                    if result:
                        _LOGGER.debug(f"Updated registry with selectedInstance: 0 (default, could not convert {device_id})")
                        return True
        except Exception as e:
            _LOGGER.error(f"Error updating registry with selectedInstance: {e}")
            return False

    elif sys.platform == "darwin":
        # macOS plist
        try:
            if device_id is None:
                # Set to all devices (-1)
                result = PlistManager.set_value(MACOS_PLIST_DOMAIN, "selectedInstance", -1)
            else:
                # Set to specific device
                try:
                    dev_id_int = int(device_id)
                    result = PlistManager.set_value(MACOS_PLIST_DOMAIN, "selectedInstance", dev_id_int)
                except (ValueError, TypeError):
                    result = PlistManager.set_value(MACOS_PLIST_DOMAIN, "selectedInstance", 0)

            if result:
                _LOGGER.debug(f"Updated plist with selectedInstance: {-1 if device_id is None else device_id}")
                return True
        except Exception as e:
            _LOGGER.error(f"Error updating plist with selectedInstance: {e}")
            return False

    return False

def add_startup_entry(app_type):
    """Add a startup entry for the specified application."""
    if sys.platform == "win32":
        if app_type == 'wls':
            path = os.path.join(os.environ["ProgramFiles"],
                               "Rainbow Music Led\\WiFi Led Studio",
                               "WiFi Led Studio.exe")
            path = f'"{path}"'
            return RegistryManager.set_value(WINDOWS_RUN_KEY_PATH, WLS_APP_NAME, path)
        else:  # rmlapp
            path = os.path.join(os.environ["ProgramFiles"],
                               "Rainbow Music Led\\bin",
                               "rmlapp.exe")
            path = f'"{path}"'
            return RegistryManager.set_value(WINDOWS_RUN_KEY_PATH, RMLAPP_NAME, path)

    elif sys.platform == "darwin":
        if app_type == 'wls':
            source = "/Applications/rmlapp.app/Contents/Resources/com.wls.startup.plist"
            return PlistManager.copy_launch_agent(source, WLS_LAUNCH_AGENT)
        else:  # rmlapp
            source = "/Applications/rmlapp.app/Contents/Resources/com.rmlapp.startup.plist"
            return PlistManager.copy_launch_agent(source, RMLAPP_LAUNCH_AGENT)

    return False

def remove_startup_entry(app_type):
    """Remove a startup entry for the specified application."""
    if sys.platform == "win32":
        if app_type == 'wls':
            return RegistryManager.delete_value(WINDOWS_RUN_KEY_PATH, WLS_APP_NAME)
        else:  # rmlapp
            return RegistryManager.delete_value(WINDOWS_RUN_KEY_PATH, RMLAPP_NAME)

    elif sys.platform == "darwin":
        if app_type == 'wls':
            return PlistManager.remove_launch_agent(WLS_LAUNCH_AGENT)
        else:  # rmlapp
            return PlistManager.remove_launch_agent(RMLAPP_LAUNCH_AGENT)

    return False

def check_startup_enabled(app_type):
    """Check if startup is enabled for the specified application."""
    if sys.platform == "win32":
        if app_type == 'wls':
            return RegistryManager.check_value_exists(WINDOWS_RUN_KEY_PATH, WLS_APP_NAME)
        else:  # rmlapp
            return RegistryManager.check_value_exists(WINDOWS_RUN_KEY_PATH, RMLAPP_NAME)

    elif sys.platform == "darwin":
        if app_type == 'wls':
            return PlistManager.check_launch_agent_exists(WLS_LAUNCH_AGENT)
        else:  # rmlapp
            return PlistManager.check_launch_agent_exists(RMLAPP_LAUNCH_AGENT)

    return False

def set_language_setting(language):
    """Set the language setting in registry/plist."""
    if language not in ["en", "vi"]:
        _LOGGER.error(f"Invalid language: {language}")
        return False

    if sys.platform == "win32":
        return RegistryManager.set_value(WINDOWS_RMLAPP_KEY_PATH, "language", language)
    elif sys.platform == "darwin":
        return PlistManager.set_value(MACOS_PLIST_DOMAIN, "language", language)
    return False