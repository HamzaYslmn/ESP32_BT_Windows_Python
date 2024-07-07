import serial
import serial.tools.list_ports
import asyncio
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
            list_ports()
        else:
            print("Invalid selection, please try again.")

async def read_from_port(ser):
    while True:
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
        ser.write((command + '\n').encode('utf-8'))
        await asyncio.sleep(0.0001)

async def main():
    port_list = list_ports()
    port = select_port(port_list)
    if port is None:
        print("No port selected")
        return

    try:
        ser = serial.Serial(port, BAUDRATE)
    except serial.SerialException as e:
        console.print(f"[red]{e}[/]")
        return

    print(f"Connected to {ser.name} at {ser.baudrate} baud\n\n")

    await asyncio.gather(
        read_from_port(ser),
        write_to_port(ser)
    )

    ser.close()

if __name__ == "__main__":
    asyncio.run(main())
