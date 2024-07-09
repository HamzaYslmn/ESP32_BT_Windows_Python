#include <Arduino.h>
#include "BluetoothSerial.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

BluetoothSerial SerialBT;
bool connected = false;
unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 5000; // 5 seconds

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // Bluetooth device name
  Serial.println("Bluetooth service started. Waiting for connections...");

  // Create RTOS tasks
  xTaskCreate(handleBluetoothTask, "BluetoothTask", 4096, NULL, 1, NULL);
  xTaskCreate(handleSerialTask, "SerialTask", 4096, NULL, 1, NULL);
  xTaskCreate(printOnlineTask, "PrintOnlineTask", 2048, NULL, 1, NULL);
}

void loop() {
  vTaskDelete(NULL); // Delete the loop task
}

void handleBluetoothTask(void * parameter) {
  while(true) {
    // Check Bluetooth connection status
    if (SerialBT.hasClient()) {
      if (!connected) {
        Serial.println("Connected to Bluetooth device");
        connected = true;
      }
      if (SerialBT.available() > 0) {
        String received = SerialBT.readStringUntil('\n');
        received.trim();
        SerialBT.println("BT Echo: " + received);
      }
    } else {
      if (connected) {
        Serial.println("Disconnected from Bluetooth device");
        connected = false;
      }
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
    vTaskDelay(4 / portTICK_PERIOD_MS); // Delay to allow other tasks to run
  }
}

void handleSerialTask(void * parameter) {
  while(true) {
    if (Serial.available() > 0) {
      String received = Serial.readStringUntil('\n');
      received.trim();
      Serial.println("Serial Echo: " + received);
    }
    vTaskDelay(4 / portTICK_PERIOD_MS); // Delay to allow other tasks to run
  }
}

void printOnlineTask(void * parameter) {
  while(true) {
    Serial.println("Online");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}
