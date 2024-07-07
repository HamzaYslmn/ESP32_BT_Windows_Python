#include "BluetoothSerial.h"

BluetoothSerial SerialBT;
bool connected = false;
unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 5000; // 5 seconds

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // Bluetooth device name
  Serial.println("Bluetooth service started. Waiting for connections...");
}

void loop() {
  // Check Bluetooth connection status
  if (SerialBT.hasClient()) {
    if (!connected) {
      Serial.println("Connected to Bluetooth device");
      connected = true;
    }
    handleBluetooth();
  } else {
    if (connected) {
      Serial.println("Disconnected from Bluetooth device");
      connected = false;
    }
    attemptReconnect();
  }
  
  // Handle serial data from USB/Serial
  handleSerial();
  
  delay(10); // Short delay to prevent busy-waiting
}

void handleBluetooth() {
  if (SerialBT.available() > 0) {
    String received = SerialBT.readString();
    received.trim();
    SerialBT.println("BT Received: " + received);
    SerialBT.println("BT Echo: " + received);
  }
}

void handleSerial() {
  if (Serial.available() > 0) {
    String received = Serial.readString();
    received.trim();
    Serial.println("Received: " + received);
    Serial.println("Serial Echo: " + received);
  }
}

void attemptReconnect() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastReconnectAttempt >= reconnectInterval) {
    lastReconnectAttempt = currentMillis;
    if (!SerialBT.hasClient()) {
      Serial.print(".");
      SerialBT.end();
      delay(100);
      SerialBT.begin("ESP32_BT");
    }
  }
}