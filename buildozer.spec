[app]

# App-Name (Anzeige auf dem Handy)
title = Archälogie

# Paketname (muss klein & ohne Umlaute sein!)
package.name = archaelogie

# Domain (frei wählbar)
package.domain = org.example

# Quellcode
source.dir = .
source.include_exts = py

# Version
version = 1.0

# Python / Kivy / Android
requirements = python3,kivy,pyjnius

# Einstiegspunkt
entrypoint = main.py

# Anzeige
fullscreen = 1
orientation = portrait

# Android SDK
android.api = 33
android.minapi = 26
android.sdk = 33
android.ndk = 25b

# ❗ WICHTIG: Berechtigungen
android.permissions = CAMERA

# Debug / Logs
android.logcat_filters = *:S python:D

# Architektur
android.archs = arm64-v8a

# Buildozer
warn_on_root = 1
