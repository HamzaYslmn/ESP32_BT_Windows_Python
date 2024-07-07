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

async def terminal_mode(ser):
    console.print("[green]Entering Terminal Mode... write 'esc' to return to the main menu.[/]")
    while True:
        command = await asyncio.to_thread(input, "")
        if command == "esc":
            break
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
        console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
        ser.write((command + '\n').encode('utf-8'))
    console.print("[yellow]Returning to main menu...[/]")

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
        ser = serial.Serial(port, BAUDRATE)
        console.clear()
        console.print(f"[green]Connected to {ser.name} at {ser.baudrate} baud[/]\n")
        await asyncio.gather(read_from_port(ser), main_menu(ser))
    except serial.SerialException as e:
        console.print(f"[red]{e}[/]")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    asyncio.run(main())
