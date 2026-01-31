[app]
title = CompassApp
package.name = compass
package.domain = org.example

source.dir = .
source.include_exts = py,kv

requirements = kivy, pyjnius

version = 1.0

android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 26
android.sdk = 33
