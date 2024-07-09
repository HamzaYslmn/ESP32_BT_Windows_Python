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
