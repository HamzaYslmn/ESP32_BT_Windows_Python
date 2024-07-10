#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

TaskHandle_t Task1;  // BLE handling task
TaskHandle_t Task2;  // Serial handling task
TaskHandle_t Task3;  // Online print task

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String value = pCharacteristic->getValue();
      if (value.length() > 0) {
        Serial.println("Received: " + String(value.c_str()));
        pCharacteristic->setValue("BT Echo: " + value);
        pCharacteristic->notify();
      }
    }
};

void setup() {
  Serial.begin(115200);

  // Create the BLE Device
  BLEDevice::init("ESP32_BLE");

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ   |
                      BLECharacteristic::PROPERTY_WRITE  |
                      BLECharacteristic::PROPERTY_NOTIFY |
                      BLECharacteristic::PROPERTY_INDICATE
                    );

  pCharacteristic->setCallbacks(new MyCallbacks());

  // Create a BLE Descriptor
  pCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  // set value to 0x00 to not advertise this parameter
  BLEDevice::startAdvertising();
  Serial.println("Waiting for a client connection to notify...");

  // Create tasks
  xTaskCreatePinnedToCore(handleBLETask, "BLETask", 8192, NULL, 1, &Task1, 1);
  xTaskCreatePinnedToCore(handleSerialTask, "SerialTask", 8192, NULL, 1, &Task2, 0);
  xTaskCreatePinnedToCore(printOnlineTask, "OnlineTask", 8192, NULL, 1, &Task3, 0);
}

void loop() {
  vTaskDelete(NULL); // Delete loop task
}

void handleBLETask(void * pvParameters) {
  while (true) {
    // Disconnecting
    if (!deviceConnected && oldDeviceConnected) {
      delay(500); // Give the bluetooth stack the chance to get things ready
      pServer->startAdvertising(); // Restart advertising
      Serial.println("Start advertising");
      oldDeviceConnected = deviceConnected;
    }
    // Connecting
    if (deviceConnected && !oldDeviceConnected) {
      oldDeviceConnected = deviceConnected;
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void handleSerialTask(void * pvParameters) {
  while (true) {
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      Serial.println("Serial Echo: " + input);
      if (deviceConnected) {
        pCharacteristic->setValue(input.c_str());
        pCharacteristic->notify();
      }
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void printOnlineTask(void * pvParameters) {
  while (true) {
    Serial.println("Online");
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}