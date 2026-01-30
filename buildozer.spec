[app]

title = Forschung
package.name = forschung
package.domain = forschung.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.9.1

requirements = python3,kivy,pyjnius,pillow,android

orientation = portrait
fullscreen = 0

# =========================
# ANDROID
# =========================

# ❗ NUR Kamera-Berechtigung
android.permissions = CAMERA

android.api = 33
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# ⚠️ GANZ WICHTIG: EINE ZEILE, KEINE LISTE
android.manifest_xml_contents = <queries><intent><action android:name="android.media.action.IMAGE_CAPTURE"/></intent></queries>

# =========================
# Python for Android
# =========================
p4a.bootstrap = sdl2


[buildozer]
log_level = 2
warn_on_root = 1
