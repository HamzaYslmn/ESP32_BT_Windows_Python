import asyncio
from bleak import BleakClient, BleakScanner
from rich.console import Console
from datetime import datetime
import keyboard
import time

console = Console()

SERVICE_UUID = "0000180D-0000-1000-8000-00805F9B34FB"  # Replace with your service UUID
CHARACTERISTIC_UUID = "00002A37-0000-1000-8000-00805F9B34FB"  # Replace with your characteristic UUID

async def list_devices():
    devices = await BleakScanner.discover()
    device_list = {}
    console.print("Available Bluetooth Devices:")
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
            await list_devices()
        else:
            console.print("Invalid selection, please try again.")

async def read_from_device(client):
    while True:
        try:
            response = await client.read_gatt_char(CHARACTERISTIC_UUID)
            response = response.decode('utf-8').strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
            
            if response not in ["x", "x"]:
                if response.startswith("BT "):
                    console.print(f"[rgb(50,160,240)]{timestamp} - {response}[/]")
                else:
                    console.print(f"[rgb(50,240,160)]{timestamp} - {response}[/]")
                    
        except Exception as e:
            console.print(f"[red]Error reading from device: {e}[/]")
        await asyncio.sleep(0.001)

async def terminal_mode(client):
    console.print("[green]Entering Terminal Mode... write 'esc' to return to the main menu.[/]")
    while True:
        command = await asyncio.to_thread(input, "")
        if command in ["esc", "q"]:
            break
        if command == "cls":
            console.clear()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
        console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
        try:
            await client.write_gatt_char(CHARACTERISTIC_UUID, (command + '\n').encode('utf-8'))
        except Exception as e:
            console.print(f"[red]Error writing to device: {e}[/]")
    console.print("[yellow]Returning to main menu...[/]")

async def keyboard_listener(client):
    keyboard_mode = True
    console.print("[yellow]Entering keyboard listening mode. Press 'esc' to exit and return to the main menu.[/]")
    
    pressed_keys = set()
    last_sent_time = 0
    send_interval = 0.01

    def on_key_event(e):
        nonlocal keyboard_mode
        if e.event_type == keyboard.KEY_DOWN:
            pressed_keys.add(e.name)
            if e.name == 'esc':
                keyboard_mode = False
                console.print("[yellow]Exiting keyboard listening mode...[/]")
        elif e.event_type == keyboard.KEY_UP:
            pressed_keys.discard(e.name)

    keyboard.hook(on_key_event)

    async def send_key_state():
        nonlocal last_sent_time
        while keyboard_mode:
            current_time = time.time()
            if current_time - last_sent_time >= send_interval:
                if pressed_keys:
                    key_string = '+'.join(sorted(pressed_keys))
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
                    console.print(f"[rgb(240,160,255)]{timestamp} - {key_string}[/]")
                else:
                    key_string = 'none'
                
                try:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, (key_string + '\n').encode('utf-8'))
                except Exception as e:
                    console.print(f"[red]Error writing to device: {e}[/]")
                
                last_sent_time = current_time
            await asyncio.sleep(0.004)

    send_task = asyncio.create_task(send_key_state())

    while keyboard_mode:
        await asyncio.sleep(0.004)
        
    send_task.cancel()
    keyboard.unhook_all()
    console.print("[yellow]Exited keyboard listening mode.[/]")

async def latency_test(client):
    latencies = []
    console.print("[yellow]Starting latency test...[/]")
    test_message = b'ping\n'
    console.print(f"[cyan]Test message size: {len(test_message)} bytes[/]")
    
    for i in range(100):
        await asyncio.sleep(0.001)
        start_time = time.perf_counter()
        try:
            await client.write_gatt_char(CHARACTERISTIC_UUID, test_message)
            response = await client.read_gatt_char(CHARACTERISTIC_UUID)
            if b"ping" in response:
                end_time = time.perf_counter()
                latencies.append((end_time - start_time) * 1000)
            if i % 10 == 9:
                console.print(f"[cyan]Completed {i+1} iterations[/]")
        except Exception as e:
            console.print(f"[red]Error during latency test: {e}[/]")
            break
    
    if latencies:
        lat_count = len(latencies)
        avg, min_lat, max_lat = sum(latencies) / lat_count, min(latencies), max(latencies)
        console.print(f"[green]Latency test completed {lat_count} iterations[/]")
        console.print(f"[yellow]Average Latency: {avg:.2f} ms[/]")
        console.print(f"[yellow]Min Latency: {min_lat:.2f} ms[/]")
        console.print(f"[yellow]Max Latency: {max_lat:.2f} ms[/]")
    else:
        console.print("[red]No valid latency measurements were recorded.[/]")

async def mbps_test(client):
    data = b'0' * 10000
    num_chunks = 100
    console.print("[yellow]Starting Mbps test...[/]")
    try:
        start_time = time.perf_counter()
        for _ in range(num_chunks):
            await client.write_gatt_char(CHARACTERISTIC_UUID, data, response=False)
        end_time = time.perf_counter()

        duration = end_time - start_time
        total_data = len(data) * num_chunks
        mbps = (total_data * 8) / (duration * 1000000)
        console.print(f"[green]Speed: {mbps:.2f} Mbps[/]")
    except Exception as e:
        console.print(f"[red]Error during Mbps test: {e}[/]")

async def main_menu(client):
    while True:
        console.print("\nMain Menu:")
        console.print("1 - Terminal Mode")
        console.print("2 - Keyboard Mode")
        console.print("3 - Mbps Test")
        console.print("4 - Latency Test")
        console.print("Press 'Enter' to clear the terminal\n")

        command = await asyncio.to_thread(input, "Select a mode: ")
        
        if command == "1":
            await terminal_mode(client)
        elif command == "2":
            await keyboard_listener(client)
        elif command == "3":
            await mbps_test(client)
        elif command == "4":
            await latency_test(client)
        elif command == "":
            console.clear()
        else:
            console.print("[red]Invalid selection, please try again.[/]")
            await asyncio.sleep(1)
            console.clear()

async def main():
    device_list = await list_devices()
    device = await select_device(device_list)
    if not device:
        console.print("[red]No device selected[/]")
        return
    try:
        async with BleakClient(device.address) as client:
            console.clear()
            console.print(f"[green]Connected to {device.name}[/]\n")
            await asyncio.gather(read_from_device(client), main_menu(client))
    except Exception as e:
        console.print(f"[red]{e}[/]")

if __name__ == "__main__":
    asyncio.run(main())