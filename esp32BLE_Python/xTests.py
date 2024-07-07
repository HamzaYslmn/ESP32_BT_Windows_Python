from rich.console import Console
import asyncio
import time

console = Console()

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