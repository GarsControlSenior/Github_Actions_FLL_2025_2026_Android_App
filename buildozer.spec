[app]

title = Forschung
package.name = forschung
package.domain = forschung.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.7.9

# Nur das Nötigste
requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

# =========================
# ANDROID
# =========================

# Nur Kamera-Berechtigung nötig
android.permissions = CAMERA

android.api = 32
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Damit die Systemkamera gefunden wird (Android 11+)
android.manifest_xml_contents = <queries><intent><action android:name="android.media.action.IMAGE_CAPTURE"/></intent></queries>

# =========================
# Python for Android
# =========================
p4a.bootstrap = sdl2


[buildozer]
log_level = 2
warn_on_root = 1
