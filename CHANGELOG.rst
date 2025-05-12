=========
Changelog
=========

Version 0.10.2
==============

- Update documentation
- Update documentation endpoints
- Update supported versions
- Drop sACN race condition error level to info

Version 0.10.1
==============

- **Bugfix release**

Version 0.10.0
==============

What's new?
-----------

- **Active development!**

  - A bunch of new developers have arrived!

- **New Effects**

  - *BPM Based Effects:* Bar, MultiBar, Strobe
  - *EQ-Like Effects:* Blocks, Equalizer
  - *Other Effects:* Power, Magnitude

- **SkydimondUSB Compatability**

  - *SkydimondUSB Device:* Use a COM port to communicate with your skydimondusb-compatible device.

- **Scenes & Presets**

  - *Scenes:* Save current effects of all devices as a *scene*, and reactivate any saved scene from the dashboard.
  - *Presets:* Effects have presets, with different settings to demo how the effect can be configured. You can save your own effect configurations as a *custom preset*.

- **Facelift.**

  - More polished interface.
  - New colour scheme.
  - More icons.

- **Device Auto Discovery:** RML devices on the network are automatically found at launch if no devices are present. Scan for RML devices in Device Management.

- **Improved Documentation:** Better guides for installation across Win, Mac, and Linux

- **Sliders:** Effect configuration needs sliders, not numbers! What year is it?

- **Polish:** Smooth transitions between effects.

- **Dark Mode:** Choose from a few different themes for the web interface.

- **Logging:** View Wls logs live from the web interface. Access full logs at  ``~/.wls/Wls.log`` (Linux/ Mac) or ``%APPDATA%/.wls/Wls.log`` (Windows)

- **Bugfixes:** Chewing through them, slow and steady!

  - IP address resolution fixed for mDNS names.
  - Broken Browser Installs (should) no longer break Wls.
  - Some rare race conditions captured.
  - Devices can now be renamed - 2021, what a year!
  - Various libraries updated for new hotness and fix underlying issues.

Known Issues
------------

- **Audio Input Handling**

  - Wls might explode if you don't have a valid audio input stream. Sorry and whoops.

- **sACN Display Rate**

  - Still fiddling with the sACN library - currently the "refresh rate" variable is a best effort FPS and is not accurate.

- **Editing active device breaks it**

  - Maybe don't do this. We're working on it!

- **Incomplete Change List**

  - We just didn't keep track! Whoops!

Coming up...
------------

- **QLC+ Support**

- **Spotify Support [Beta]**

- **Effects Rewrite:** Build and customise your own effects from a palette of effect sources and colour mappings.

- **ColorChord effect:** Clone of `cnlohr's ColorChord <https://github.com/cnlohr/colorchord>`_ notefinding algorithm.

- **Missing a feature you'd love to see?** `Let us know on Discord <https://discord.gg/xyyHEquZKQ>`_!

Other News
----------

.. _Wls Website: https://wls.app
.. |Wls Website| replace:: **Wls Website**

- |Wls Website|_: We now have a website! Not much going on here save for hosting the Windows installer downloads.

- **Easy Windows Installation.** Windows users can download an installer that automatically updates Wls with the latest features for you. `Windows installer download <https://wls.app/download/>`_

- **Automatic crash reporting with Sentry:** If something breaks, we'll know about it! Any errors will be automatically transmitted to the developers
  so we can fix them - in the unlikely event any sensitive personal data is transmitted with a crash report the developers will remove it as soon as possible.
  The crash reporter we use is Sentry - you can see their `privacy policy <https://sentry.io/privacy/>`_ that developers are held to. The Wls privacy policy
  is pretty simple - we will use the logs to fix Wls. We don't use any user analytics, user tracking or any of that.


----------------------------------------------


Version 0.11.0
=============

- If device is RML & active effect, than display RML info

Version 0.9.2
=============

- **High Priority Bugfix.**

Version 0.9.1
=============
- **Bugfixes.**

Version 0.9.0
=============

- **Sliders.** Effect configuration needs sliders, not numbers! What year is it?
- **Polish.** Smooth transitions between effects.
- **Automatic Updates.** Installable EXE will automatically update itself at launch if there's a new version available

Version 0.8.0
=============

- **New Effects**
    - *BPM Based Effects:* Bar, MultiBar, Strobe
    - *EQ-Like Effects:* Blocks, Equalizer
    - *Other Effects:* Power, Magnitude
- **Scenes & Presets**
    - *Scenes:* Save current effects of all devices as a *scene*, and reactivate any saved scene from the dashboard.
    - *Presets:* Effects have presets, with different settings to demo how the effect can be configured. You can save your own effect configurations as a *custom preset*.
- **Facelift.**
    - More polished interface.
    - New colour scheme.
    - More icons.
- **Device Auto Discovery.** RML devices on the network are automatically found at launch if no devices are present. Scan for RML devices in Device Management.
- **Improved Documentation.** better guides for installation across Win, Mac, and Linux

Version 0.7.0
=============

- Updating React and front end dependencies
- separated JS code from PY code moved front end to top level folder
- Removed webpack in favor of CRA for less complexity and faster dev work

Version 0.2.0
=============

- More effects and support for UDP devices
- Frontend converted to react and more features added

Version 0.1.0
=============

- **Initial release with basic feature set!**
    - Added a framework for highly customizable effects and outputs
    - Added some basic effects and audio reaction ones