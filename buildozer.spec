[app]

# Title of your application
title = Forschung

# Package name
package.name = forschung

# Package domain
package.domain = forschung.test

# Source code directory
source.dir = .

# Source files to include
source.include_exts = py,png,jpg,kv,atlas

# Version
version = 0.7

# ✅ Anforderungen
# pyjnius ist NOTWENDIG für Android-Intents (Kamera)
requirements = python3,kivy,pyjnius,plyer,pillow

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0


#
# Android specific
#

# ✅ BENÖTIGTE PERMISSIONS
android.permissions = CAMERA

# Target API (Play-Store-konform)
android.api = 33

# Minimum API
android.minapi = 21

# NDK API
android.ndk_api = 21

# CPU Archs
android.archs = arm64-v8a, armeabi-v7a

# Backup erlauben
android.allow_backup = True


#
# Python-for-Android
#

# Standard Bootstrap (empfohlen)
p4a.bootstrap = sdl2


[buildozer]

log_level = 2
warn_on_root = 1
