import asyncio
import time
from rich.console import Console
import keyboard
from datetime import datetime

console = Console()

async def keyboard_listener(ser):
    keyboard_mode = True
    console.print("[yellow]Entering keyboard listening mode. Type 'exit_keyboard_mode' to return to main menu.[/]")
    
    pressed_keys = set()
    last_sent_time = 0
    send_interval = 0.01  # 10ms interval

    def on_key_event(e):
        nonlocal pressed_keys, last_sent_time
        if e.event_type == keyboard.KEY_DOWN:
            pressed_keys.add(e.name)
        elif e.event_type == keyboard.KEY_UP:
            pressed_keys.discard(e.name)

    keyboard.hook(on_key_event)

    async def send_key_state():
        nonlocal pressed_keys, last_sent_time
        while keyboard_mode:
            current_time = time.time()
            if current_time - last_sent_time >= send_interval:
                if pressed_keys:
                    key_string = '+'.join(sorted(pressed_keys))
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
                    console.print(f"[rgb(240,160,255)]{timestamp} - {key_string}[/]")
                    ser.write((key_string + '\n').encode('utf-8'))
                last_sent_time = current_time
            await asyncio.sleep(0.001)  # 1ms sleep to allow other tasks to run

    send_task = asyncio.create_task(send_key_state())

    while keyboard_mode:
        command = await asyncio.to_thread(input, "")
        if command == "exit_keyboard_mode":
            keyboard_mode = False
        elif command:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
            console.print(f"[rgb(240,160,255)]{timestamp} - {command}[/]")
            ser.write((command + '\n').encode('utf-8'))

    send_task.cancel()
    keyboard.unhook_all()
    console.print("[yellow]Exited keyboard listening mode.[/]")