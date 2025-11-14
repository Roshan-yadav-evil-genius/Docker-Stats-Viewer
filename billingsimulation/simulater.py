import time
import requests
import os
import threading
import math

# Global list to keep memory blocks referenced
memory_blocks = []

def consume_ram(size_mb=200):
    """Allocate memory in MB and keep it referenced"""
    print(f"[RAM] Allocating {size_mb} MB...")
    block = "X" * (size_mb * 1024 * 1024)
    memory_blocks.append(block)  # Keep reference to prevent garbage collection
    return block

def consume_cpu(duration=10):
    """Perform CPU-intensive calculations"""
    print(f"[CPU] Starting CPU-intensive work for {duration} seconds...")
    start = time.time()
    while time.time() - start < duration:
        # Perform mathematical calculations to consume CPU
        for i in range(10000):
            math.sqrt(i * 3.14159)
            math.sin(i * 0.1)
            math.cos(i * 0.1)

def consume_disk(size_mb=50):
    """Create and write files to consume disk I/O"""
    print(f"[DISK] Writing {size_mb} MB to disk...")
    filename = f"/tmp/test_file_{int(time.time())}.bin"
    
    # Write data to disk
    with open(filename, 'wb') as f:
        data = b'X' * (1024 * 1024)  # 1MB chunks
        for _ in range(size_mb):
            f.write(data)
            f.flush()  # Force write to disk
    
    # Read it back to consume more I/O
    with open(filename, 'rb') as f:
        while f.read(1024 * 1024):  # Read in 1MB chunks
            pass
    
    # Clean up
    os.remove(filename)

def consume_bandwidth(url="https://httpbin.org/bytes/10485760", duration=30):
    """Download repeatedly for given seconds"""
    print(f"[NET] Downloading from {url} for {duration} seconds...")
    start = time.time()
    bytes_downloaded = 0
    
    while time.time() - start < duration:
        try:
            r = requests.get(url, stream=True, timeout=10)
            r.raise_for_status()
            
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    bytes_downloaded += len(chunk)
                    # Simulate processing the data
                    _ = chunk.decode('utf-8', errors='ignore')
                    
        except Exception as e:
            print(f"[NET] Error downloading: {e}")
            time.sleep(1)  # Wait before retrying
    
    print(f"[NET] Downloaded {bytes_downloaded / (1024*1024):.2f} MB")

def consume_all_resources(ram_mb=200, cpu_duration=10, disk_mb=50, net_duration=30):
    """Consume all resources simultaneously using threads"""
    print("[ALL] Starting comprehensive resource consumption...")
    
    threads = []
    
    # Memory consumption (main thread)
    mem_thread = threading.Thread(target=lambda: consume_ram(ram_mb))
    threads.append(mem_thread)
    
    # CPU consumption
    cpu_thread = threading.Thread(target=lambda: consume_cpu(cpu_duration))
    threads.append(cpu_thread)
    
    # Disk consumption
    disk_thread = threading.Thread(target=lambda: consume_disk(disk_mb))
    threads.append(disk_thread)
    
    # Network consumption
    net_thread = threading.Thread(target=lambda: consume_bandwidth(duration=net_duration))
    threads.append(net_thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("[ALL] Resource consumption cycle completed")
