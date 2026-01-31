[app]

title = CompassApp
package.name = compass
package.domain = org.example

source.include_exts = py,png,kv

requirements = kivy, pyjnius

android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION

android.api = 33
android.minapi = 26
android.sdk = 32
