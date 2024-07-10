#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

#define SERVICE_UUID        "0000180D-0000-1000-8000-00805F9B34FB"
#define CHARACTERISTIC_UUID "00002A37-0000-1000-8000-00805F9B34FB"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("Connected to BLE device");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("Disconnected from BLE device");
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String rxValue = pCharacteristic->getValue().c_str();
      if (rxValue.length() > 0) {
        Serial.print("Received: ");
        Serial.println(rxValue);
        String response = "BT Echo: " + rxValue;
        pCharacteristic->setValue(response.c_str());
        pCharacteristic->notify();
      }
    }
};

void bleTask(void * parameter) {
  for(;;) {
    if (deviceConnected) {
      // BLE device is connected, handle any BLE-specific tasks here
    }
    
    if (!deviceConnected && oldDeviceConnected) {
      delay(500); // give the bluetooth stack the chance to get things ready
      pServer->startAdvertising(); // restart advertising
      Serial.println("Start advertising");
      oldDeviceConnected = deviceConnected;
    }
    
    if (deviceConnected && !oldDeviceConnected) {
      oldDeviceConnected = deviceConnected;
    }
    
    vTaskDelay(pdMS_TO_TICKS(10)); // 10ms delay
  }
}

void serialTask(void * parameter) {
  for(;;) {
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      Serial.print("Serial Echo: ");
      Serial.println(input);
      
      if (deviceConnected) {
        pCharacteristic->setValue(input.c_str());
        pCharacteristic->notify();
      }
    }
    vTaskDelay(pdMS_TO_TICKS(4)); // 4ms delay
  }
}

void onlineTask(void * parameter) {
  for(;;) {
    Serial.println("Online");
    vTaskDelay(pdMS_TO_TICKS(1000)); // 1 second delay
  }
}

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
  xTaskCreatePinnedToCore(
    bleTask,    // Function to implement the task
    "BLETask",  // Name of the task
    10000,      // Stack size in words
    NULL,       // Task input parameter
    1,          // Priority of the task
    NULL,       // Task handle
    1);         // Core where the task should run

  xTaskCreatePinnedToCore(
    serialTask, // Function to implement the task
    "SerialTask", // Name of the task
    10000,      // Stack size in words
    NULL,       // Task input parameter
    1,          // Priority of the task
    NULL,       // Task handle
    0);         // Core where the task should run

  xTaskCreatePinnedToCore(
    onlineTask, // Function to implement the task
    "OnlineTask", // Name of the task
    10000,      // Stack size in words
    NULL,       // Task input parameter
    1,          // Priority of the task
    NULL,       // Task handle
    0);         // Core where the task should run
}

void loop() {
  // Empty. Things are done in Tasks.
  vTaskDelete(NULL);
}