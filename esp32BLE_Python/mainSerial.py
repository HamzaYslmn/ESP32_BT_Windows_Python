import serial
import serial.tools.list_ports
import asyncio
from rich.console import Console
from datetime import datetime
import keyboard
import time

BAUDRATE = 115200
console = Console()

def list_ports():
    ports = serial.tools.list_ports.comports()
    port_list = {}
    console.print("Available COM Ports:")
    for index, port in enumerate(ports, start=1):
        console.print(f"{index} - {port.device}: {port.description}")
        port_list[index] = port.device
    return port_list

def select_port(port_list):
    while True:
        selection = input("Select the port number: ")
        if selection.isdigit() and int(selection) in port_list:
            return port_list[int(selection)]
        elif selection == "0" or len(selection) == 0:
            console.clear()
            list_ports()
        else:
            console.print("Invalid selection, please try again.")

async def read_from_port(ser):
    while True:
        try:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
                
                if response not in [".", "Online"]:
                    if response.startswith("BT "):
                        console.print(f"[rgb(50,160,240)]{timestamp} - {response}[/]")
                    else:
                        console.print(f"[rgb(50,240,160)]{timestamp} - {response}[/]")
                        
        except Exception as e:
            console.print(f"[red]Error reading from port: {e}[/]")
        await asyncio.sleep(0.001)

async def terminal_mode(ser):
    console.print("[green]Entering Terminal Mode... write 'esc' to return to the main menu.[/]")
    while True:
        command = await asyncio.to_thread(input, "")
        if command == "esc" or command == "q":
            break
        if command == "cls":
            console.clear()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
        console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
        try:
            ser.write((command + '\n').encode('utf-8'))
            ser.flush()
        except Exception as e:
            console.print(f"[red]Error writing to port: {e}[/]")
    console.print("[yellow]Returning to main menu...[/]")
    
async def keyboard_listener(ser):
    keyboard_mode = True
    console.print("[yellow]Entering keyboard listening mode. Press 'esc' to exit and return to the main menu.[/]")
    
    pressed_keys = set()
    last_sent_time = 0
    send_interval = 0.01  # Increased to 10ms to avoid overwhelming the buffer

    def on_key_event(e):
        nonlocal keyboard_mode
        if e.event_type == keyboard.KEY_DOWN:
            pressed_keys.add(e.name)
            if e.name == 'esc':  # Check if the pressed key is 'esc'
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
                    ser.write((key_string + '\n').encode('utf-8'))
                    ser.flush()  # Ensure data is sent out immediately
                except Exception as e:
                    console.print(f"[red]Error writing to port: {e}[/]")
                
                last_sent_time = current_time
            await asyncio.sleep(0.004)  # 4ms sleep to allow other tasks to run

    send_task = asyncio.create_task(send_key_state())

    while keyboard_mode:
        await asyncio.sleep(0.004)  # 4ms polling to prevent blocking
        
    send_task.cancel()
    keyboard.unhook_all()
    console.print("[yellow]Exited keyboard listening mode.[/]")
    
async def latency_test(ser):
    latencies = []
    console.print("[yellow]Starting latency test...[/]")
    test_message = b'ping\n'
    console.print(f"[cyan]Test message size: {len(test_message)} bytes[/]")
    
    for i in range(100):
        await asyncio.sleep(0.001)  # Reduced sleep time for better responsiveness
        start_time = time.perf_counter()
        try:
            ser.write(test_message)
            ser.flush()  # Ensure data is sent out immediately
            while True:
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    if "ping" in response:
                        end_time = time.perf_counter()
                        latencies.append((end_time - start_time) * 1000)
                        break
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
    ser.reset_input_buffer()

async def mbps_test(ser):
    data = b'0' * 10000  # 10KB of data, smaller chunk size for USB
    num_chunks = 100  # Send 100 chunks for a total of 1MB
    console.print("[yellow]Starting Mbps test...[/]")
    try:
        start_time = time.perf_counter()
        for _ in range(num_chunks):
            ser.write(data)
            ser.flush()  # Ensure data is sent out immediately
        end_time = time.perf_counter()

        duration = end_time - start_time
        total_data = len(data) * num_chunks
        mbps = (total_data * 8) / (duration * 1000000)
        console.print(f"[green]Speed: {mbps:.2f} Mbps[/]")
    except Exception as e:
        console.print(f"[red]Error during Mbps test: {e}[/]")
    
    ser.reset_input_buffer()

async def main_menu(ser):
    while True:
        console.print("\nMain Menu:")
        console.print("1 - Terminal Mode")
        console.print("2 - Keyboard Mode")
        console.print("3 - Mbps Test")
        console.print("4 - Latency Test")
        console.print("Press 'Enter' to clear the terminal\n")

        command = await asyncio.to_thread(input, "Select a mode: ")
        
        if command == "1":
            await terminal_mode(ser)

        elif command == "2":
            await keyboard_listener(ser)

        elif command == "3":
            await mbps_test(ser)

        elif command == "4":
            await latency_test(ser)

        elif command == "":
            console.clear()

        else:
            console.print("[red]Invalid selection, please try again.[/]")
            await asyncio.sleep(1)
            console.clear()

async def main():
    port_list = list_ports()
    port = select_port(port_list)
    if not port:
        console.print("[red]No port selected[/]")
        return
    try:
        ser = serial.Serial(port, BAUDRATE, timeout=5)  # Increased timeout value
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        console.clear()
        console.print(f"[green]Connected to {ser.name} at {ser.baudrate} baud[/]\n")
        await asyncio.gather(read_from_port(ser), main_menu(ser))
    except serial.SerialException as e:
        console.print(f"[red]{e}[/]")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            console.print("[yellow]Serial port closed.[/]")

if __name__ == "__main__":
    asyncio.run(main())
    