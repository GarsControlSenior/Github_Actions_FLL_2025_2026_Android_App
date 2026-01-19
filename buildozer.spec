[app]

title = Forschung

package.name = forschung
package.domain = forschung.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.7.5

# 🔑 WICHTIG: pyjnius für Android-Intent
requirements = python3,kivy,pyjnius,plyer,pillow

orientation = portrait
fullscreen = 0


#
# Android specific
#

# 📷 Kamera-Berechtigung (Popup beim ersten Start)
android.permissions = CAMERA

android.api = 33
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True


#
# Python-for-Android
#
p4a.bootstrap = sdl2


[buildozer]

log_level = 2
warn_on_root = 1
