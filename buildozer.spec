[app]

title = Forschung
package.name = forschung
package.domain = forschung.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.7.9

# Alle benötigten Pakete: Kivy für GUI, pyjnius für Java-Brücke, Pillow für Bildbearbeitung
requirements = python3,kivy,pyjnius,Pillow,android

orientation = portrait
fullscreen = 0

# =========================
# ANDROID
# =========================

# Kamera + Speicher-Berechtigungen
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 32
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Damit die Kamera-App gefunden wird (Android 11+)
android.manifest_xml_contents = <queries><intent><action android:name="android.media.action.IMAGE_CAPTURE"/></intent></queries>

# =========================
# Python for Android
# =========================
p4a.bootstrap = sdl2


[buildozer]
log_level = 2
warn_on_root = 1
