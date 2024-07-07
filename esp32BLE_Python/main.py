import serial
import serial.tools.list_ports
import asyncio
from rich.console import Console
from datetime import datetime
from xTests import latency_test, mbps_test
from xKeyboardMode import keyboard_listener

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
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
            if response.startswith("BT "):
                console.print(f"[rgb(50,160,240)]{timestamp} - {response}[/]")
            else:
                console.print(f"[rgb(50,240,160)]{timestamp} - {response}[/]")
        await asyncio.sleep(0.0001)

async def main_menu(ser):
    while True:
        command = await asyncio.to_thread(input, "")
        if command == "cls":
            console.clear()
        elif command == "latency_test":
            await latency_test(ser)
        elif command == "mbps_test":
            await mbps_test(ser)
        elif command == "keyboard_mode":
            await keyboard_listener(ser)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
            console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
            ser.write((command + '\n').encode('utf-8'))

async def main():
    port_list = list_ports()
    port = select_port(port_list)
    if not port:
        console.print("[red]No port selected[/]")
        return
    try:
        ser = serial.Serial(port, BAUDRATE)
        console.clear()
        console.print(f"[green]Connected to {ser.name} at {ser.baudrate} baud[/]\n")
        console.print("[yellow]Type 'keyboard_mode' to enter keyboard listening mode.[/]")
        await asyncio.gather(read_from_port(ser), main_menu(ser))
    except serial.SerialException as e:
        console.print(f"[red]{e}[/]")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    asyncio.run(main())