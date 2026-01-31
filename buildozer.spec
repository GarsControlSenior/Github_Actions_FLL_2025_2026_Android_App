[app]

# App-Name (wird auf dem Handy angezeigt)
title = Archälogie

# Paketname (muss klein bleiben!)
package.name = archaelogie

# Domain
package.domain = org.example

# Pfad zu main.py
source.dir = .
source.include_exts = py

# Version
version = 1.0

# Python / Kivy
requirements = python3,kivy,pyjnius

# Startdatei
entrypoint = main.py

# Bildschirm
fullscreen = 1
orientation = portrait

# Android Einstellungen
android.api = 33
android.minapi = 26
android.sdk = 33
android.ndk = 25b

# Berechtigungen
android.permissions = CAMERA

# Logs
android.logcat_filters = *:S python:D

# Architektur
android.archs = arm64-v8a

warn_on_root = 1
