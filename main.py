import docker
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime

IMAGE_NAME = "billingsimulation"
CONTAINER_NAME = "billingsimulation_live"

client = docker.from_env()

# -------------------------------------------------------------------
#  Create container if not exists (or replace it)
# -------------------------------------------------------------------
def ensure_container():
    try:
        old = client.containers.get(CONTAINER_NAME)
        print("[+] Old container found. Removing...")
        old.stop()
        old.remove()
    except docker.errors.NotFound:
        print("[+] No old container. Creating fresh one...")
    except Exception as e:
        print("[-] Unexpected error:", e)

    try:
        print("[+] Creating new container from image:", IMAGE_NAME)
        container = client.containers.run(
            IMAGE_NAME,
            name=CONTAINER_NAME,
            detach=True,
            command=["python", "-u", "main.py"]
        )
        print("[+] Container started:", CONTAINER_NAME)
        return container
    except docker.errors.ImageNotFound:
        raise Exception(f"Image '{IMAGE_NAME}' not found.")
    except Exception as e:
        raise Exception("[-] Failed to create container: " + str(e))


container = ensure_container()
stats_stream = container.stats(stream=True)


# -------------------------------------------------------------------
#  CPU calculation identical to Docker Desktop
# -------------------------------------------------------------------
def calculate_cpu_percent(stats):
    try:
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_usage = cpu_stats.get("cpu_usage", {})
        precpu_usage = precpu_stats.get("cpu_usage", {})

        total_usage = cpu_usage.get("total_usage", 0)
        pre_total_usage = precpu_usage.get("total_usage", 0)

        system_cpu = cpu_stats.get("system_cpu_usage", 0)
        pre_system_cpu = precpu_stats.get("system_cpu_usage", 0)

        if system_cpu == 0 or pre_system_cpu == 0:
            return cpu_stats["cpu_usage"].get("total_usage", 0) / 1e7

        cpu_delta = total_usage - pre_total_usage
        system_delta = system_cpu - pre_system_cpu

        cpu_count = cpu_stats.get("online_cpus") or \
                    len(cpu_stats["cpu_usage"].get("percpu_usage", [])) or 1

        if cpu_delta > 0 and system_delta > 0:
            return (cpu_delta / system_delta) * cpu_count * 100
    except:
        pass

    return 0


# -------------------------------------------------------------------
#  Extract usable stats from docker json
# -------------------------------------------------------------------
def format_stats(stat):
    cpu = calculate_cpu_percent(stat)

    mem_used = stat["memory_stats"]["usage"]
    mem_limit = stat["memory_stats"]["limit"]

    try:
        net = list(stat["networks"].values())[0]
        rx = net["rx_bytes"]
        tx = net["tx_bytes"]
    except:
        rx = tx = 0

    try:
        blk = stat["blkio_stats"]["io_service_bytes_recursive"]
        read = blk[0]["value"] if blk else 0
        write = blk[1]["value"] if blk else 0
    except:
        read = write = 0

    return {
        "cpu": cpu,
        "mem_used": mem_used / (1024**3),
        "mem_limit": mem_limit / (1024**3),
        "rx": rx,
        "tx": tx,
        "read": read / (1024**2),
        "write": write / 1024
    }


# -------------------------------------------------------------------
#  Buffers
# -------------------------------------------------------------------
timestamps = []
cpu_vals = []
mem_vals = []
rx_vals = []
tx_vals = []
read_vals = []
write_vals = []


# -------------------------------------------------------------------
#  Animation loop
# -------------------------------------------------------------------
def animate(i):
    try:
        stat = json.loads(next(stats_stream))
        s = format_stats(stat)

        # Append timestamp
        timestamps.append(datetime.now().strftime("%H:%M:%S"))

        # Append stats
        cpu_vals.append(s["cpu"])
        mem_vals.append(s["mem_used"])
        rx_vals.append(s["rx"])
        tx_vals.append(s["tx"])
        read_vals.append(s["read"])
        write_vals.append(s["write"])

        # Keep buffer size manageable
        max_len = 200
        for arr in [timestamps, cpu_vals, mem_vals, rx_vals, tx_vals, read_vals, write_vals]:
            if len(arr) > max_len:
                arr.pop(0)

        # Clear plots
        ax1.clear(); ax2.clear(); ax3.clear(); ax4.clear()

        # ---- CPU ----
        ax1.plot(timestamps, cpu_vals)
        ax1.set_title(f"CPU Usage: {cpu_vals[-1]:.2f}%",color="red",bbox=dict(facecolor="black", edgecolor="none", pad=4))
        ax1.set_ylim(0, max(cpu_vals + [10]) * 1.2)
        ax1.tick_params(axis='x', rotation=45)

        # ---- Memory ----
        ax2.plot(timestamps, mem_vals)
        ax2.set_title(f"Memory Usage: {mem_vals[-1]:.2f}GB / {s['mem_limit']:.2f}GB",
        color="red",bbox=dict(facecolor="black", edgecolor="none", pad=4))
        ax2.set_ylim(0, max(mem_vals + [1]) * 1.2)
        ax2.tick_params(axis='x', rotation=45)

        # ---- Disk I/O ----
        ax3.plot(timestamps, read_vals, label="Read (MB)")
        ax3.plot(timestamps, write_vals, label="Write (KB)")
        ax3.set_title(
            f"Disk IO: {read_vals[-1]:.2f}MB / {write_vals[-1]:.2f}KB",
            color="red",bbox=dict(facecolor="black", edgecolor="none", pad=4)
        )

        ax3.set_ylim(0, max(max(read_vals), max(write_vals)) * 1.2)
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)

        # ---- Network I/O ----
        ax4.plot(timestamps, rx_vals, label="RX (bytes)")
        ax4.plot(timestamps, tx_vals, label="TX (bytes)")
        ax4.set_title(
    f"Network IO: {rx_vals[-1]/1024:.2f}KB / {tx_vals[-1]/1024:.2f}KB",
    color="red",bbox=dict(facecolor="black", edgecolor="none", pad=4)
)

        ax4.set_ylim(0, max(max(rx_vals), max(tx_vals)) * 1.2)
        ax4.legend()
        ax4.tick_params(axis='x', rotation=45)

    except StopIteration:
        print("[-] Stats stream ended.")
        return


# -------------------------------------------------------------------
#  Plot layout
# -------------------------------------------------------------------
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle("LIVE Docker Stats Dashboard (Dynamic Scaling)", fontsize=16)

ani = animation.FuncAnimation(fig, animate, interval=900)
plt.tight_layout()
plt.show()
