#include "BluetoothSerial.h"
#include <Arduino.h>

BluetoothSerial SerialBT;
bool connected = false;
unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 5000; // 5 seconds

TaskHandle_t Task1;  // Bluetooth handling task
TaskHandle_t Task2;  // Serial handling task
TaskHandle_t Task3;  // Online print task

SemaphoreHandle_t serialMutex;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // Bluetooth device name
  Serial.println("Bluetooth service started. Waiting for connections...");

  // Create the mutex before using it
  serialMutex = xSemaphoreCreateMutex();

  // Create a task that will handle Bluetooth communication
  xTaskCreatePinnedToCore(
    handleBluetoothTask,   /* Task function */
    "BluetoothTask",       /* name of task */
    10000,                 /* Stack size of task */
    NULL,                  /* parameter of the task */
    1,                     /* priority of the task */
    &Task1,                /* Task handle */
    0);                    /* pin task to core 0 */

  // Create a task that will handle Serial communication
  xTaskCreatePinnedToCore(
    handleSerialTask,      /* Task function */
    "SerialTask",          /* name of task */
    10000,                 /* Stack size of task */
    NULL,                  /* parameter of the task */
    1,                     /* priority of the task */
    &Task2,                /* Task handle */
    1);                    /* pin task to core 1 */

  // Create a task that will print "Online" every 1000ms
  xTaskCreatePinnedToCore(
    printOnlineTask,       /* Task function */
    "OnlineTask",          /* name of task */
    10000,                 /* Stack size of task */
    NULL,                  /* parameter of the task */
    1,                     /* priority of the task */
    &Task3,                /* Task handle */
    1);                    /* pin task to core 1 */
}

void loop() {
  // Do nothing in the main loop
}

void handleBluetoothTask(void * pvParameters) {
  vTaskDelay(45); 
  for (;;) {
    // Check Bluetooth connection status
    if (SerialBT.hasClient()) {
      if (!connected) {
        xSemaphoreTake(serialMutex, portMAX_DELAY);
        Serial.println("Connected to Bluetooth device");
        xSemaphoreGive(serialMutex);
        connected = true;
      }
      if (SerialBT.available() > 0) {
        String received = SerialBT.readStringUntil('\n');
        received.trim();
        xSemaphoreTake(serialMutex, portMAX_DELAY);
        SerialBT.println("BT Echo: " + received);
        xSemaphoreGive(serialMutex);
      }
    } else {
      if (connected) {
        xSemaphoreTake(serialMutex, portMAX_DELAY);
        Serial.println("Disconnected from Bluetooth device");
        xSemaphoreGive(serialMutex);
        connected = false;
      }
      attemptReconnect();
    }
    vTaskDelay(4 / portTICK_PERIOD_MS);
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

void handleSerialTask(void * pvParameters) {
  for (;;) {
    if (Serial.available() > 0) {
      String received = Serial.readStringUntil('\n');
      received.trim();
      xSemaphoreTake(serialMutex, portMAX_DELAY);
      Serial.println("Serial Echo: " + received);
      xSemaphoreGive(serialMutex);
    }
    vTaskDelay(4 / portTICK_PERIOD_MS);
  }
}

void printOnlineTask(void * pvParameters) {
  for (;;) {
    xSemaphoreTake(serialMutex, portMAX_DELAY);
    Serial.println("Online");
    xSemaphoreGive(serialMutex);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}


