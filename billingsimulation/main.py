import time
from simulater import consume_all_resources, consume_ram, consume_cpu, consume_disk, consume_bandwidth


def main():
    x = 0
    print("=== Resource Consumption Script Started ===")
    print("This script will consume CPU, Memory, Disk, and Network resources")
    
    while True:
        print(f"\n=== Cycle {x} ===")
        try:
            # Option 1: Consume all resources simultaneously (recommended)
            consume_all_resources(
                ram_mb=1024*5,      # 500 MB RAM
                cpu_duration=20, # 20 seconds of CPU work
                disk_mb=100,     # 100 MB disk I/O
                net_duration=30  # 30 seconds of network activity
            )
            
            # Option 2: Sequential resource consumption (uncomment to use instead)
            # print("Sequential resource consumption:")
            # consume_ram(500)
            # consume_cpu(20)
            # consume_disk(100)
            # consume_bandwidth(duration=30)
            
            x += 1
            print(f"Cycle {x-1} completed. Starting next cycle in 5 seconds...")
            time.sleep(5)  # Brief pause between cycles
            
        except KeyboardInterrupt:
            print("\nScript interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"Error in cycle {x}: {e}")
            print("Waiting 60 seconds before retrying...")
            time.sleep(60)


if __name__ == "__main__":
    main()