import docker
from docker.client import DockerClient
from docker.models.containers import Container
import json
import sys

def get_docker_client():
    """Get Docker client with proper error handling"""
    try:
        client = docker.from_env()
        # Test the connection
        client.ping()
        print("[+] Docker daemon is running and accessible")
        return client
    except docker.errors.DockerException as e:
        print(f"[-] Docker daemon is not available: {e}")
        print("[-] Please ensure Docker Desktop is running")
        return None
    except Exception as e:
        print(f"[-] Unexpected error connecting to Docker: {e}")
        return None

client = get_docker_client()


def imageExist(client: DockerClient):
    if client is None:
        print("[-] Docker client is not available")
        return False
    try:
        client.images.get("billingsimulation")
        print("[+] theoneeyecore Image Found")
        return True
    except docker.errors.ImageNotFound as e:
        print("[-] theoneeyecore Image Not Found")
        return False



def initiateContainer(client: DockerClient)->Container:
    if client is None:
        raise ValueError("Docker client is not available")
    print("[+] Executing theoneeyecore Image")
    container = client.containers.run(
        image="billingsimulation",
        detach=True,
        command=[
            "sh", "-c",
            """
            # Run main script
            python -u  main.py
            """
        ]
    )
    return container

def monitorUsage(container: Container, output_file="usage.jl"):
    stats_stream = container.stats(stream=True)
    with open(output_file, "a") as f:   # append mode
        for stat in stats_stream:
            data = json.loads(stat)
            f.write(json.dumps(data) + "\n")   # one line per stat
            f.flush()  # make sure it writes immediately
        


if client is not None:
    if imageExist(client):
        container = initiateContainer(client)
        monitorUsage(container)
    else:
        print("[-] Cannot proceed without the required Docker image")
        sys.exit(1)
else:
    print("[-] Cannot proceed without Docker daemon")
    print("[-] Please start Docker Desktop and try again")
    sys.exit(1)

