# Sau khi sao chép WiFi Led Studio.app vào rmlapp.app/Contents/Resources/
codesign --deep --force --verify --verbose --timestamp \
         --options runtime \
         --entitlements "/Users/phamtuantrung/make setup/entitlements.xml" \
         --sign "Developer ID Application: Pham Tuan Trung (P6B7T335D8)" \
         "/Users/phamtuantrung/make setup/WiFi Led Studio.app"

cp -R "/Users/phamtuantrung/make setup/WiFi Led Studio.app" "/Users/phamtuantrung/make setup/rmlapp.app/Contents/Resources/"
cp -R "/Users/phamtuantrung/make setup/restart.scpt" "/Users/phamtuantrung/make setup/rmlapp.app/Contents/Resources/"
cp -R "/Users/phamtuantrung/make setup/com.rmlapp.startup.plist" "/Users/phamtuantrung/make setup/rmlapp.app/Contents/Resources/"
cp -R "/Users/phamtuantrung/make setup/com.wls.startup.plist" "/Users/phamtuantrung/make setup/rmlapp.app/Contents/Resources/"

cp -R "/Users/phamtuantrung/make setup/WiFi Led Studio.app" "/Users/phamtuantrung/make setup/m1/rmlapp.app/Contents/Resources/"
cp -R "/Users/phamtuantrung/make setup/restart.scpt" "/Users/phamtuantrung/make setup/m1/rmlapp.app/Contents/Resources/"
cp -R "/Users/phamtuantrung/make setup/com.rmlapp.startup.plist" "/Users/phamtuantrung/make setup/m1/rmlapp.app/Contents/Resources/"
cp -R "/Users/phamtuantrung/make setup/com.wls.startup.plist" "/Users/phamtuantrung/make setup/m1/rmlapp.app/Contents/Resources/"

codesign --force --verify --verbose --timestamp --options runtime --sign "Developer ID Application: Pham Tuan Trung (P6B7T335D8)" /Users/phamtuantrung/make\ setup/rmlapp.app/Contents/plugins/tls/libqopensslbackend.dylib
codesign --force --verify --verbose --timestamp --options runtime --sign "Developer ID Application: Pham Tuan Trung (P6B7T335D8)" /Users/phamtuantrung/make\ setup/m1/rmlapp.app/Contents/plugins/tls/libqopensslbackend.dylib

codesign --deep --force --verify --verbose --timestamp \
         --options runtime \
         --entitlements "/Users/phamtuantrung/make setup/entitlements.xml" \
         --sign "Developer ID Application: Pham Tuan Trung (P6B7T335D8)" \
         "/Users/phamtuantrung/make setup/rmlapp.app"

codesign --deep --force --verify --verbose --timestamp \
         --options runtime \
         --entitlements "/Users/phamtuantrung/make setup/entitlements.xml" \
         --sign "Developer ID Application: Pham Tuan Trung (P6B7T335D8)" \
         "/Users/phamtuantrung/make setup/m1/rmlapp.app"