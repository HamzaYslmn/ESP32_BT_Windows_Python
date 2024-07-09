import asyncio
import time
from rich.console import Console
import keyboard
from datetime import datetime

console = Console()

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