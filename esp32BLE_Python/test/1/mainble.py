import asyncio
from bleak import BleakClient, BleakScanner
from rich.console import Console

console = Console()

SERVICE_UUID = "12345678-1234-1234-1234-123456789012"
CHARACTERISTIC_UUID = "87654321-4321-4321-4321-210987654321"

async def list_devices():
    devices = await BleakScanner.discover()
    device_list = {}
    console.print("Available BLE Devices:")
    for index, device in enumerate(devices, start=1):
        console.print(f"{index} - {device.name}: {device.address}")
        device_list[index] = device
    return device_list

async def select_device(device_list):
    while True:
        selection = input("Select the device number: ")
        if selection.isdigit() and int(selection) in device_list:
            return device_list[int(selection)]
        elif selection == "0" or len(selection) == 0:
            console.clear()
            device_list = await list_devices()
        else:
            console.print("Invalid selection, please try again.")

async def run():
    device_list = await list_devices()
    selected_device = await select_device(device_list)

    async with BleakClient(selected_device.address) as client:
        # Check if the characteristic supports notify
        services = await client.get_services()
        for service in services:
            if service.uuid == SERVICE_UUID:
                for char in service.characteristics:
                    if char.uuid == CHARACTERISTIC_UUID and 'notify' in char.properties:
                        console.print(f"Characteristic {CHARACTERISTIC_UUID} supports notify")
                        break
                else:
                    console.print(f"Characteristic {CHARACTERISTIC_UUID} does not support notify")
                    return
                break
        else:
            console.print(f"Service {SERVICE_UUID} not found")
            return

        def handle_data(sender, data):
            console.print(f"Received: {data.decode('utf-8')}")

        await client.start_notify(CHARACTERISTIC_UUID, handle_data)

        while True:
            user_input = input("Enter a string to send to ESP32: ")
            await client.write_gatt_char(CHARACTERISTIC_UUID, user_input.encode())
            await asyncio.sleep(1)

asyncio.run(run())
