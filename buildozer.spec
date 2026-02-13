[app]

# Name der App (wird auf dem Handy angezeigt)
title = Archäologie

# Paketname (muss klein sein, keine Umlaute!)
package.name = archaelogie

# Domain (frei wählbar)
package.domain = org.example

# Quellcode
source.dir = .
source.include_exts = py

# Version
version = 1.0

# Einstiegspunkt
entrypoint = main.py

# Benötigte Bibliotheken
requirements = python3, kivy, opencv-python-headless, numpy, plyer, pillow, android

# Anzeige
fullscreen = 0
orientation = portrait

# Android SDK / NDK
android.api = 33
android.minapi = 24
android.sdk = 33
android.ndk = 25b

# Berechtigungen
android.permissions = CAMERA, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Architektur
android.archs = arm64-v8a, armeabi-v7a

# Debug (optional)
android.logcat_filters = *:S python:D

# Buildozer
warn_on_root = 1


# Erlaubt das Speichern von Dateien
android.allow_backup = True
