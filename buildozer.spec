[app]

title = CompassApp
package.name = compassapp
package.domain = test.compass

source.dir = .
source.include_exts = py

version = 0.1

requirements = python3,kivy,plyer

orientation = portrait
fullscreen = 0

# Android BLE Berechtigungen
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,ACCESS_FINE_LOCATION

android.api = 32
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
