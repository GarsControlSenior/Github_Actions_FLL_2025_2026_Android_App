[app]

title = Forschung
package.name = forschung
package.domain = forschung.test

source.dir = .
source.include_exts = py

version = 0.7.9

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 32
android.minapi = 21
android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a

p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
