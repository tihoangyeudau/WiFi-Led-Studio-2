"""
Global hotkey manager for WiFi Led Studio 2
Provides cross-platform hotkey functionality using pynput
"""

import logging
import sys
from typing import Dict, Callable, Optional
from pynput.keyboard import GlobalHotKeys

_LOGGER = logging.getLogger(__name__)


class HotkeyManager:
    """
    Cross-platform global hotkey manager for WLS
    """

    def __init__(self, wls_core):
        self.wls_core = wls_core
        self.hotkeys: Optional[GlobalHotKeys] = None
        self.hotkey_mappings: Dict[str, Callable] = {}
        self.enabled = True

        # Default hotkey combinations
        self.default_hotkeys = {
            # Toggle LED on/off
            '<ctrl>+<alt>+t': self._toggle_led_state,

            # Brightness controls
            '<ctrl>+<alt>+<up>': self._increase_brightness,
            '<ctrl>+<alt>+<down>': self._decrease_brightness,

            # Effect controls
            '<ctrl>+<alt>+<right>': self._next_effect,
            '<ctrl>+<alt>+<left>': self._previous_effect,

            # Quick effects
            '<ctrl>+<alt>+1': self._quick_effect_rainbow,
            '<ctrl>+<alt>+2': self._quick_effect_strobe,
            '<ctrl>+<alt>+3': self._quick_effect_fade,
            '<ctrl>+<alt>+4': self._quick_effect_energy,

            # Screen capture
            '<ctrl>+<alt>+x': self._screen_capture,

            # Open web interface
            '<ctrl>+<alt>+w': self._open_web_interface,
        }

        # Load custom hotkeys from config
        self._load_hotkeys_from_config()

    def _load_hotkeys_from_config(self):
        """Load hotkey mappings from configuration"""
        try:
            # Load hotkey settings from config
            hotkey_config = self.wls_core.config.get('hotkey_settings', {})

            # Check if hotkeys are enabled - prioritize registry setting over config
            try:
                from wls.platform_utils import get_hotkeys_enabled_setting
                self.enabled = get_hotkeys_enabled_setting()
                _LOGGER.debug(f"Loaded hotkeys enabled state from registry: {self.enabled}")
            except Exception as e:
                # Fallback to config setting if registry fails
                self.enabled = hotkey_config.get('enabled', True)
                _LOGGER.debug(f"Fallback to config hotkeys enabled state: {self.enabled}")
                _LOGGER.debug(f"Registry read error: {e}")

            # Load custom hotkey mappings
            custom_hotkeys = hotkey_config.get('mappings', {})

            # Start with defaults and override with custom mappings
            self.hotkey_mappings = self.default_hotkeys.copy()

            # Convert custom string mappings to actual functions
            for hotkey, action in custom_hotkeys.items():
                if isinstance(action, str):
                    callback = self._get_callback_from_action_name(action)
                    if callback:
                        self.hotkey_mappings[hotkey] = callback
                    else:
                        _LOGGER.warning(f"Unknown action '{action}' for hotkey '{hotkey}'")
                else:
                    # Direct function mapping
                    self.hotkey_mappings[hotkey] = action

            _LOGGER.debug(f"Loaded {len(self.hotkey_mappings)} hotkey mappings (enabled: {self.enabled})")

        except Exception as e:
            _LOGGER.error(f"Error loading hotkeys from config: {e}")
            self.hotkey_mappings = self.default_hotkeys.copy()
            self.enabled = True

    def start(self):
        """Start the global hotkey listener"""
        if not self.enabled:
            return

        try:
            # Create hotkey mappings with error handling
            safe_mappings = {}
            for hotkey, callback in self.hotkey_mappings.items():
                safe_mappings[hotkey] = self._safe_callback(callback)

            self.hotkeys = GlobalHotKeys(safe_mappings)
            self.hotkeys.start()

            _LOGGER.info(f"Global hotkeys started with {len(safe_mappings)} combinations")

            # Log available hotkeys for user reference
            self._log_available_hotkeys()

        except Exception as e:
            _LOGGER.error(f"Failed to start global hotkeys: {e}")
            if sys.platform == "darwin":
                _LOGGER.warning(
                    "On macOS, you may need to grant accessibility permissions to Python. "
                    "Go to System Preferences > Security & Privacy > Privacy > Accessibility "
                    "and add your Python executable or terminal application."
                )

        # Save current state to config
        self._save_hotkey_state_to_config()

    def stop(self):
        """Stop the global hotkey listener"""
        try:
            if self.hotkeys:
                self.hotkeys.stop()
                self.hotkeys = None
                _LOGGER.info("Global hotkeys stopped")
        except Exception as e:
            _LOGGER.error(f"Error stopping global hotkeys: {e}")

    def _safe_callback(self, callback: Callable) -> Callable:
        """Wrap callback with error handling"""
        def safe_wrapper():
            try:
                callback()
            except Exception as e:
                _LOGGER.error(f"Error in hotkey callback: {e}")
        return safe_wrapper

    def _log_available_hotkeys(self):
        """Log available hotkeys for user reference"""
        _LOGGER.info("Available global hotkeys:")
        hotkey_descriptions = {
            '<ctrl>+<alt>+t': 'Toggle LED on/off',
            '<ctrl>+<alt>+<up>': 'Increase brightness',
            '<ctrl>+<alt>+<down>': 'Decrease brightness',
            '<ctrl>+<alt>+<right>': 'Next effect',
            '<ctrl>+<alt>+<left>': 'Previous effect',
            '<ctrl>+<alt>+1': 'Rainbow effect',
            '<ctrl>+<alt>+2': 'Strobe effect',
            '<ctrl>+<alt>+3': 'Fade effect',
            '<ctrl>+<alt>+4': 'Energy effect',
            '<ctrl>+<alt>+x': 'Screen capture',
            '<ctrl>+<alt>+w': 'Open web interface',
        }

        for hotkey, description in hotkey_descriptions.items():
            if hotkey in self.hotkey_mappings:
                _LOGGER.info(f"  {hotkey}: {description}")

    def _save_hotkey_state_to_config(self):
        """Save hotkey state and mappings to configuration"""
        try:
            # Update config with current hotkey settings
            if 'hotkey_settings' not in self.wls_core.config:
                self.wls_core.config['hotkey_settings'] = {}

            self.wls_core.config['hotkey_settings']['enabled'] = self.enabled

            # Save current hotkey mappings as serializable format
            mappings = {}
            for hotkey, callback in self.hotkey_mappings.items():
                # Convert function callbacks to string identifiers
                action_name = self._get_action_name_from_callback(callback)
                if action_name:
                    mappings[hotkey] = action_name

            self.wls_core.config['hotkey_settings']['mappings'] = mappings

            # Save config
            from wls.config import save_config
            save_config(self.wls_core.config, self.wls_core.config_dir)

            # Also save enabled state to registry/plist
            try:
                from wls.platform_utils import set_hotkeys_enabled_setting
                if set_hotkeys_enabled_setting(self.enabled):
                    _LOGGER.debug(f"Updated registry with hotkeysEnabled={self.enabled}")
                else:
                    _LOGGER.error(f"Failed to update registry with hotkeysEnabled={self.enabled}")
            except Exception as e:
                _LOGGER.error(f"Error updating registry hotkeys setting: {e}")

            _LOGGER.debug(f"Saved {len(mappings)} hotkey mappings to config")

        except Exception as e:
            _LOGGER.error(f"Error saving hotkey state to config: {e}")

    def _get_action_name_from_callback(self, callback):
        """Convert callback function to string identifier"""
        try:
            # Check if it's one of our standard methods
            method_mapping = {
                self._toggle_led_state: 'toggle_led_state',
                self._increase_brightness: 'increase_brightness',
                self._decrease_brightness: 'decrease_brightness',
                self._next_effect: 'next_effect',
                self._previous_effect: 'previous_effect',
                self._screen_capture: 'screen_capture',
                self._open_web_interface: 'open_web_interface',
                self._quick_effect_rainbow: 'quick_effect_rainbow',
                self._quick_effect_strobe: 'quick_effect_strobe',
                self._quick_effect_fade: 'quick_effect_fade',
                self._quick_effect_energy: 'quick_effect_energy',
            }

            if callback in method_mapping:
                return method_mapping[callback]

            # Check if it's a lambda for quick effects
            if hasattr(callback, '__name__') and callback.__name__ == '<lambda>':
                # Try to extract effect name from lambda
                # This is a bit tricky, but we can check the closure
                if hasattr(callback, '__closure__') and callback.__closure__:
                    for cell in callback.__closure__:
                        if isinstance(cell.cell_contents, str):
                            return f'effect_{cell.cell_contents}'

            # For other cases, try to get function name
            if hasattr(callback, '__name__'):
                return callback.__name__

        except Exception as e:
            _LOGGER.debug(f"Could not get action name for callback: {e}")

        return None

    def _get_callback_from_action_name(self, action_name):
        """Convert string action name to callback function"""
        try:
            # Standard method mappings
            method_mapping = {
                'toggle_led_state': self._toggle_led_state,
                'increase_brightness': self._increase_brightness,
                'decrease_brightness': self._decrease_brightness,
                'next_effect': self._next_effect,
                'previous_effect': self._previous_effect,
                'screen_capture': self._screen_capture,
                'open_web_interface': self._open_web_interface,
                'quick_effect_rainbow': self._quick_effect_rainbow,
                'quick_effect_strobe': self._quick_effect_strobe,
                'quick_effect_fade': self._quick_effect_fade,
                'quick_effect_energy': self._quick_effect_energy,
            }

            if action_name in method_mapping:
                return method_mapping[action_name]

            # Effect actions
            if action_name.startswith('effect_'):
                effect_name = action_name[7:]  # Remove 'effect_' prefix
                return lambda: self._apply_quick_effect(effect_name)

            # Try to get method by name (with underscore prefix)
            if hasattr(self, f'_{action_name}'):
                return getattr(self, f'_{action_name}')

        except Exception as e:
            _LOGGER.debug(f"Could not get callback for action '{action_name}': {e}")

        return None

    # Hotkey callback methods
    def _toggle_led_state(self):
        """Toggle LED state on/off"""
        _LOGGER.debug("Hotkey: Toggle LED state")
        self.wls_core.toggle_led_state()

    def _increase_brightness(self):
        """Increase brightness by 10%"""
        current_brightness_percent = self.wls_core.get_current_brightness()  # Returns 0-100
        current_brightness = current_brightness_percent / 100.0  # Convert to 0.0-1.0
        new_brightness = min(1.0, current_brightness + 0.1)
        _LOGGER.debug(f"Hotkey: Increase brightness to {int(new_brightness * 100)}%")
        self.wls_core.set_brightness(new_brightness)

    def _decrease_brightness(self):
        """Decrease brightness by 10%"""
        current_brightness_percent = self.wls_core.get_current_brightness()  # Returns 0-100
        current_brightness = current_brightness_percent / 100.0  # Convert to 0.0-1.0
        new_brightness = max(0.0, current_brightness - 0.1)
        _LOGGER.debug(f"Hotkey: Decrease brightness to {int(new_brightness * 100)}%")
        self.wls_core.set_brightness(new_brightness)

    def _next_effect(self):
        """Switch to next effect"""
        _LOGGER.debug("Hotkey: Next effect")
        self._cycle_effect(direction=1)

    def _previous_effect(self):
        """Switch to previous effect"""
        _LOGGER.debug("Hotkey: Previous effect")
        self._cycle_effect(direction=-1)

    def _cycle_effect(self, direction: int):
        """Cycle through available effects"""
        try:
            if not hasattr(self.wls_core, 'effects') or not self.wls_core.effects:
                return

            # Get list of available effects from registry
            available_effects = [effect for effect in self.wls_core.effects.classes().keys() if effect != 'screen_capture']
            if not available_effects:
                return

            # Find current effect index
            current_effect = self.wls_core.current_effect
            current_index = 0

            if current_effect and current_effect in available_effects:
                current_index = available_effects.index(current_effect)

            # Calculate next index
            next_index = (current_index + direction) % len(available_effects)
            next_effect = available_effects[next_index]

            # Apply the effect
            self.wls_core.apply_effect_to_all(next_effect)
            _LOGGER.info(f"Switched to effect: {next_effect}")

        except Exception as e:
            _LOGGER.error(f"Error cycling effects: {e}")

    def _apply_quick_effect(self, effect_name: str):
        """Apply a specific effect quickly"""
        _LOGGER.debug(f"Hotkey: Apply effect {effect_name}")
        try:
            # Normalize effect name
            normalized_effect = self.wls_core._normalize_effect_type(effect_name)
            if normalized_effect:
                self.wls_core.apply_effect_to_all(normalized_effect)
            else:
                _LOGGER.warning(f"Effect '{effect_name}' not found")
        except Exception as e:
            _LOGGER.error(f"Error applying quick effect {effect_name}: {e}")

    # Quick effect methods for serialization
    def _quick_effect_rainbow(self):
        """Apply rainbow effect"""
        self._apply_quick_effect('rainbow')

    def _quick_effect_strobe(self):
        """Apply strobe effect"""
        self._apply_quick_effect('strobe')

    def _quick_effect_fade(self):
        """Apply fade effect"""
        self._apply_quick_effect('fade')

    def _quick_effect_energy(self):
        """Apply energy effect"""
        self._apply_quick_effect('energy')

    def _screen_capture(self):
        """Start screen capture mode"""
        _LOGGER.debug("Hotkey: Screen capture")
        try:
            self.wls_core.stop_aw(0)
            _LOGGER.info("Started screen capture mode via hotkey")
        except Exception as e:
            _LOGGER.error(f"Error starting screen capture: {e}")

    def _open_web_interface(self):
        """Open the web interface in default browser"""
        _LOGGER.debug("Hotkey: Open web interface")
        try:
            import webbrowser
            url = f"http://{self.wls_core.host}:{self.wls_core.port}"
            webbrowser.open(url)
            _LOGGER.info(f"Opened web interface: {url}")
        except Exception as e:
            _LOGGER.error(f"Error opening web interface: {e}")

    def enable(self):
        """Enable hotkeys"""
        self.enabled = True
        if not self.hotkeys:
            self.start()
        self._save_hotkey_state_to_config()

    def disable(self):
        """Disable hotkeys"""
        self.enabled = False
        self.stop()
        self._save_hotkey_state_to_config()

    def is_enabled(self) -> bool:
        """Check if hotkeys are enabled"""
        return self.enabled and self.hotkeys is not None

    def add_custom_hotkey(self, hotkey: str, callback: Callable):
        """Add a custom hotkey mapping"""
        try:
            self.hotkey_mappings[hotkey] = callback

            # Restart hotkeys to include new mapping
            if self.hotkeys:
                self.stop()
                self.start()

            _LOGGER.info(f"Added custom hotkey: {hotkey}")

        except Exception as e:
            _LOGGER.error(f"Error adding custom hotkey {hotkey}: {e}")

    def remove_hotkey(self, hotkey: str):
        """Remove a hotkey mapping"""
        try:
            if hotkey in self.hotkey_mappings:
                del self.hotkey_mappings[hotkey]

                # Restart hotkeys to remove mapping
                if self.hotkeys:
                    self.stop()
                    self.start()

                _LOGGER.info(f"Removed hotkey: {hotkey}")
            else:
                _LOGGER.warning(f"Hotkey not found: {hotkey}")

        except Exception as e:
            _LOGGER.error(f"Error removing hotkey {hotkey}: {e}")