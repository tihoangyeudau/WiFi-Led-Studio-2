@echo off

taskkill /f /im "ambilightwifid.exe" /t > NUL
wait
start "" "C:\Program Files (x86)\WiFi Led Studio\WiFi Led Studio.exe" --open-ui

exit /B