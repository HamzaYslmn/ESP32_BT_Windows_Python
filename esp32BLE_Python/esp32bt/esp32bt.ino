#include "BluetoothSerial.h"
#include <Arduino.h>

BluetoothSerial SerialBT;
bool connected = false;
unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 5000; // Slightly more than 5 seconds to avoid overlap

TaskHandle_t Task1;  // Bluetooth handling task
TaskHandle_t Task2;  // Serial handling task
TaskHandle_t Task3;  // Online print task

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // Bluetooth device name
  Serial.println("Bluetooth service started. Waiting for connections...");

  // Create a task that will handle Bluetooth communication
  xTaskCreatePinnedToCore(
    handleBluetoothTask,   // Task function
    "BluetoothTask",       // name of task
    8192,                  // Stack size of task
    NULL,                  // parameter of the task
    1,                     // priority of the task
    &Task1,                // Task handle
    1);                    // pin task to core 1  Because Bluetooth is on core 1

  // Create a task that will handle Serial communication
  xTaskCreatePinnedToCore(
    handleSerialTask,      // Task function
    "SerialTask",          // name of task
    8192,                  // Stack size of task
    NULL,                  // parameter of the task
    1,                     // priority of the task
    &Task2,                // Task handle
    0);                    // pin task to core 0

  delay(45);

  // Create a task that will print "Online" every 1000ms
  xTaskCreatePinnedToCore(
    printOnlineTask,       // Task function
    "OnlineTask",          // name of task
    8192,                  // Stack size of task
    NULL,                  // parameter of the task
    1,                     // priority of the task
    &Task3,                // Task handle
    0);                    // pin task to core 0
}

void loop() {
  vTaskDelete(NULL); // Delete loop task
}

void handleBluetoothTask(void * pvParameters) {
  while (true) {
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
      attemptReconnect();
    }
    vTaskDelay(pdMS_TO_TICKS(4)); // Adjust delay as needed
  }
}

void attemptReconnect() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastReconnectAttempt >= reconnectInterval) {
    lastReconnectAttempt = currentMillis;
    if (!SerialBT.hasClient()) {
      Serial.println(".");
      SerialBT.end();
      vTaskDelay(pdMS_TO_TICKS(1000)); 
      SerialBT.begin("ESP32_BT");
    }
  }
}

void handleSerialTask(void * pvParameters) {
  while (true) {
    if (Serial.available() > 0) {
      String received = Serial.readStringUntil('\n');
      received.trim();
      Serial.println("Serial Echo: " + received);
    }
    vTaskDelay(pdMS_TO_TICKS(4));
  }
}

void printOnlineTask(void * pvParameters) {
  while (true) {
    Serial.println("\nOnline");
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}
