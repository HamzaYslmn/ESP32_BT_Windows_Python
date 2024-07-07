import serial
import serial.tools.list_ports
import asyncio
import time
from rich.console import Console
from datetime import datetime

BAUDRATE = 115200
console = Console()

def list_ports():
    ports = serial.tools.list_ports.comports()
    port_list = {}
    print("Available COM Ports:")
    for index, port in enumerate(ports, start=1):
        print(f"{index} - {port.device}: {port.description}")
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
            print("Invalid selection, please try again.")

async def read_from_port(ser):
    while True:
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
            if response.startswith("BT "):
                console.print(f"[rgb(50,160,240)]{timestamp} - {response}[/]")
            else:
                console.print(f"[rgb(50,240,160)]{timestamp} - {response}[/]")
        await asyncio.sleep(0.0001)

async def write_to_port(ser):
    while True:
        command = await asyncio.to_thread(input, "")
        if command == "cls":
            console.clear()
            continue
        elif command == "latency_test":
            await latency_test(ser)
            continue
        elif command == "mbps_test":
            await mbps_test(ser)
            continue
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
        console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
        ser.write((command + '\n').encode('utf-8'))
        await asyncio.sleep(0.0001)

async def latency_test(ser):
    latencies = []
    console.print("[yellow]Starting latency test...[/]")
    test_message = b'ping\n'
    console.print(f"[cyan]Test message size: {len(test_message)} bytes[/]")
    
    for i in range(100):
        await asyncio.sleep(0.01)
        start_time = time.perf_counter()
        ser.write(test_message)
        received = ser.readline().decode('utf-8').strip()
        echo = ser.readline().decode('utf-8').strip()
        end_time = time.perf_counter()
        
        if received == "BT Received: ping" and echo == "BT Echo: ping":
            latencies.append((end_time - start_time) * 1000)
        
        if i % 10 == 9:
            console.print(f"[cyan]Completed {i+1} iterations[/]")
    
    if latencies:
        lat_count = len(latencies)
        avg, min_lat, max_lat = sum(latencies) / len(latencies), min(latencies), max(latencies)
        console.print(f"[green]Latency test completed {lat_count} iterations[/]")
        console.print(f"[yellow]Average Latency: {avg:.2f} ms[/]")
        console.print(f"[yellow]Min Latency: {min_lat:.2f} ms[/]")
        console.print(f"[yellow]Max Latency: {max_lat:.2f} ms[/]")
    else:
        console.print("[red]No valid latency measurements were recorded.[/]")
    ser.reset_input_buffer()

async def mbps_test(ser):
    data = b'0' * 1000000  # 1MB of data
    start_time = time.perf_counter()
    ser.write(data)
    ser.readline()  # Wait for acknowledgement
    duration = time.perf_counter() - start_time
    mbps = (len(data) * 8) / (duration * 1000000)
    console.print(f"[green]Speed: {mbps:.2f} Mbps[/]")
    ser.reset_input_buffer()

async def main():
    port_list = list_ports()
    port = select_port(port_list)
    if not port:
        console.print("[red]No port selected[/]")
        return
    try:
        ser = serial.Serial(port, BAUDRATE)
        console.print(f"[green]Connected to {ser.name} at {ser.baudrate} baud[/]\n")
        await asyncio.gather(read_from_port(ser), write_to_port(ser))
    except serial.SerialException as e:
        console.print(f"[red]{e}[/]")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    asyncio.run(main())