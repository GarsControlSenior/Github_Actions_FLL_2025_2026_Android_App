[app]

title = Forschung

package.name = forschung
package.domain = forschung.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.7.8

# 🔑 WICHTIG: pyjnius für Android-Intent
requirements = python3,kivy,pyjnius,plyer,pillow

orientation = portrait
fullscreen = 0


#
# Android specific
#

# 📷 Kamera-Berechtigung (Popup beim ersten Start)
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# 3. Das "Sichtbarkeitsproblem" lösen (Queries)
# Dies erlaubt deiner App, die Kamera-App des Systems zu finden
android.manifest_xml_contents = ["<queries><intent><action android:name=\"android.media.action.IMAGE_CAPTURE\" /></intent></queries>"]
#
# Python-for-Android
#
p4a.bootstrap = sdl2


[buildozer]

log_level = 2
warn_on_root = 1
