#include <ArduinoBLE.h>
#include <Arduino_BMI270_BMM150.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// -------------------- OLED --------------------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// -------------------- LEDs --------------------
const int LED_GRUEN = 5;
const int LED_ROT   = 6;
const float TOLERANZ = 1.0;

// -------------------- BLE --------------------
BLEService dataService("180A"); // Beispiel-Service
BLEFloatCharacteristic angleChar("2A57", BLERead | BLENotify);

float winkel = 0;

// -------------------- Richtung --------------------
String directionFromAngle(float a) {
  if (a >= 337 || a < 22) return "Nord";
  if (a < 67) return "Nordost";
  if (a < 112) return "Ost";
  if (a < 157) return "Suedost";
  if (a < 202) return "Sued";
  if (a < 247) return "Suedwest";
  if (a < 292) return "West";
  return "Nordwest";
}

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(LED_GRUEN, OUTPUT);
  pinMode(LED_ROT, OUTPUT);

  // IMU starten
  if (!IMU.begin()) {
    Serial.println("IMU Fehler!");
    while (1);
  }

  // Display starten
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Display Fehler!");
    while (1);
  }

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  // BLE starten
  if (!BLE.begin()) {
    Serial.println("BLE Fehler!");
    while (1);
  }

  BLE.setLocalName("Arduino_GCS");
  BLE.setDeviceName("Arduino_GCS");
  BLE.setAdvertisedService(dataService);

  dataService.addCharacteristic(angleChar);
  BLE.addService(dataService);

  angleChar.writeValue(0.0);
  BLE.advertise();

  Serial.println("System gestartet");
}

void loop() {
  BLE.poll();

  float ax, ay, az;

  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(ax, ay, az);

    // Winkel berechnen
    winkel = atan2(ax, az) * 180.0 / PI;

    // LED Logik
    if (abs(winkel) <= TOLERANZ) {
      digitalWrite(LED_GRUEN, HIGH);
      digitalWrite(LED_ROT, LOW);
    } else {
      digitalWrite(LED_GRUEN, LOW);
      digitalWrite(LED_ROT, HIGH);
    }

    // BLE senden
    angleChar.writeValue(winkel);

    // Serial Monitor: nur Richtung
    String richtung = directionFromAngle(winkel);
    Serial.print("Richtung: ");
    Serial.println(richtung);

    // OLED Display: Winkel anzeigen
    display.clearDisplay();
    display.setTextSize(2);
    display.setCursor(0, 0);
    display.println("Winkel");

    display.setCursor(0, 30);
    display.print(winkel, 1);
    display.print(" deg");

    display.display();
  }

  delay(200);
}
