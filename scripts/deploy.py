# fbpython /Users/albertocutone/local/projects/petlog/scripts/deploy.py --run "python3 /home/metal/projects/petlog/main.py"

import argparse
import subprocess

# --- CONFIGURATION ---
MAC_PROJECT_PATH = "/Users/albertocutone/local/projects/petlog/"
PI_USER = "metal"
PI_HOST = "192.168.1.74"
PI_PROJECT_PATH = "/home/metal/projects/petlog/"
PI_HOSTNAME = f"{PI_USER}@{PI_HOST}"


def main():
    parser = argparse.ArgumentParser(
        description="Deploy project to Raspberry Pi and optionally run a command."
    )
    parser.add_argument(
        "--run",
        metavar="CMD",
        type=str,
        help="Command to run on the Pi after deployment",
    )
    args = parser.parse_args()

    # 1. rsync local project to Pi
    rsync_cmd = [
        "rsync",
        "-avz",
        "--exclude",
        ".git",
        MAC_PROJECT_PATH,
        f"{PI_HOSTNAME}:{PI_PROJECT_PATH}",
    ]
    print("Syncing project to Pi...")
    subprocess.run(rsync_cmd, check=True)
    print("rsync complete.")

    # 2. chmod (example: make all .py files executable)
    chmod_cmd = f"chmod -R u+x {PI_PROJECT_PATH}*.py"
    print(f"Setting execute permissions on {PI_PROJECT_PATH}*.py ...")
    subprocess.run(["ssh", PI_HOSTNAME, chmod_cmd], check=True)
    print("chmod complete.")

    # 3. Optionally run a command on the Pi
    if args.run:
        print(f"Running command on Pi: {args.run}")
        subprocess.run(["ssh", PI_HOSTNAME, args.run], check=True)
        print("Remote command complete.")

    print("Deployment finished.")


if __name__ == "__main__":
    main()
