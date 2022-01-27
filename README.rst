=====================================================
   Welcome to Wls ✨ *-Making music come alive!*
=====================================================
|Build Status| |License| |Build Status Docs| |Discord|
|Contributor Covenant|

.. image:: https://i.imgur.com/SFWfhFr.png

Wls website: https://wls.app/

What is Wls?
----------------

What Wls offers is the ability to take audio input, and instantaneously processes the audio into realtime light show to multiple LED strips/matrix.
No need to spend hours on end to program one song to program your LEDs, as Wls will do this all for you!

Wls real-time LED strip music visualization effect controller using is a network based devices (ESP8266/ESP32/Raspberry Pi 4) with support for advanced real-time audio effects! Wls can control multiple devices and works great with cheap ESP8266/ESP32 nodes allowing for cost effective synchronized effects across your entire house!

Demos
-------

We are actively adding and perfecting the effects, but here is a quick demo of Wls running three different effects synced across three different ESP8266 devices:

.. image:: https://raw.githubusercontent.com/Wls/Wls/gh-pages-old/demos/wls_demo-small.gif

📑 Quick start guide and documentation📖
------------------------------------------
Windows users can use the installer from the Wls website: https://wls.app/download/

Mac and Linux are also supported, though currently do not have installers.
For detailed installation instructions, see the `installation documentation`_.

😍 Show me how to make one!
-----------------------------

The below image describes a basic setup - Wls running on PC, communicating with a RML Device controlling an LED strip.

.. image:: https://i.imgur.com/vzyHNwG.png

.. list-table::
   :widths: 75 75
   :header-rows: 1

   * - Component
     - Example
   * - Computer running Wls
     - Windows 10, `Wls.exe`_
   * - Networked device controlling LED Strip
     - ESP8266 NODEMCU v3 running `RML`_
   * - Addressable LED strip
     - DC5V WS2812B 5 meters 60LED/m IP67
   * - Power supply for LED Strip and ESP
     - 5V 10 amps LED Power Supply
   * - Something to connect the wires together!
     - Soldering iron/solder

#. **Build your networked LED Strip.**
      - For most, this is the difficult step. Don't worry! There's guides here and online, and plenty of people able to help on RML and Wls Discord.
      - Follow the RML guide to connect the LED strip and ESP together: https://github.com/Aircoookie/RML/wiki.
      - Flash RML to the ESP device: https://github.com/Aircoookie/RML/wiki/Install-RML-binary
      - Ensure all RML devices are powered on, and connected to your Wi-Fi.
      - Test you can access the RML web interface from your PC. If so, then you're good to go!

#. **Install Wls.**
      - After you have RML installed on your ESP device, download: `Wls.exe`_ and install Wls.
      - For Mac and Linux, see the `installation documentation`_ or `Wls Guide`_.

#. **Direct computer audio output to Wls.**
      - Follow guide, `How to: Enable Stereo Mix in Windows 10`_.
      - Alternatively use `Voicemeeter`_. `Voicemeeter tutorial`_.
      - More information for `Linux and macOS users here <https://wls.readthedocs.io/en/latest/directing_audio.html>`_.
      - Play some music in the background.

#. **Start Wls.**
      - Your RML devices should appear in Wls, automagically configured and ready to go! 🎆🔥
      - If not, on the left hand side, click on Device Management -> ``Find RML devices`` button, or ``Add Device`` to add them manually.
      - If they're still not showing up, make sure they're powered on and properly connected to your WiFi.

#. **Start using effects!**
      - Click on the device, select an effect eg ``scroll(Reactive)``, and press ``Set effect`` button.
      - Your lights should now be reacting realtime to your music! Enjoy the show 🌈


🧑‍💻 Join the Wls Community
------------------------------

Join the Discord server to discuss everything about Wls!  |Discord|

To join, click on the Discord button below:

.. image:: https://discordapp.com/api/guilds/469985374052286474/widget.png?style=banner2
   :width: 30%
   :target: https://discord.com/invite/xyyHEquZKQ

Contributing
--------------
Pull requests are welcome. Once tested, contact Wls developer community on Discord to discuss the next step.
We expect and require all contributors to read, understand and follow our code of conduct.

Credits: `Contributors-&-About`_

License
---------
`MIT`_


.. _`MIT`: https://choosealicense.com/licenses/mit/
.. _`Wls.exe`: https://wls.app/download/
.. _`Wls Guide`: https://wls.readthedocs.io/en/dev/index.html
.. _`RML`: https://github.com/Aircoookie/RML/wiki
.. _`installation documentation`: https://wls.readthedocs.io/en/dev/installing.html
.. _`Contributors-&-About`: https://wls.app/about/
.. _`How to: Enable Stereo Mix in Windows 10`: https://thegeekpage.com/stereo-mix/
.. _`Voicemeeter`: https://vb-audio.com/Voicemeeter/index.htm
.. _`Voicemeeter tutorial`: https://youtu.be/ZXKDzYXS60o?start=27&end=163

.. |Build Status| image:: https://github.com/Wls/Wls/actions/workflows/ci-build.yml/badge.svg
   :target: https://github.com/Wls/Wls/actions/workflows/ci-build.yml
   :alt: Build Status
.. |Build Status Docs| image:: https://readthedocs.org/projects/wls/badge/?version=dev
   :target: https://wls.readthedocs.io/
   :alt: Documentation Status
.. |License| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :alt: License
.. |Discord| image:: https://img.shields.io/badge/chat-on%20discord-7289da.svg
   :target: https://discord.gg/xyyHEquZKQ
   :alt: Discord
.. |Contributor Covenant| image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
   :target: CODE_OF_CONDUCT.md