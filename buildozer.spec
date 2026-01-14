[app]

# (str) Title of your application
title = Forschung



# (str) Package name
package.name = forschung

# (str) Package domain (needed for android/ios packaging)
package.domain = forschung.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin, venv

# (str) Application versioning (method 1)
version = 0.7

# (list) Application requirements
# HINWEIS: 'android' ZWINGEND hinzugefügt, 'pillow' für Ihre Bildverarbeitung bestätigt.
requirements = python3,kivy,android,pillow,plyer,opencv-python,numpy

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# Kamera und Speicherzugriff für das Speichern von 'foto.png'
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
# ZWINGEND AUF MINDESTENS 33 ERHÖHT (Bessere Gradle-Stabilität und Google Play Store-Anforderungen)
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (bool) If True, then skip trying to update the Android sdk
# android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only. If set to False,
# the default, you will be shown the license when first running
# buildozer.
# android.accept_sdk_license = False

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True


#
# Python for android (p4a) specific
#

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2


# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer
android.permissions = CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33


# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin
