#!/usr/bin/env python3

import argparse
import subprocess
import sys

# --- CONFIGURATION ---
MAC_PROJECT_PATH = "/Users/albertocutone/local/projects/petlog/"
PI_USER = "metal"
PI_HOST = "192.168.1.74"
PI_PROJECT_PATH = "/home/metal/projects/petlog/"
PI_HOSTNAME = f"{PI_USER}@{PI_HOST}"


def run_ssh_command(command: str, description: str) -> bool:
    """Run a command on the Raspberry Pi via SSH."""
    print(f"{description}...")
    try:
        # Allow real-time output streaming to terminal
        result = subprocess.run(["ssh", PI_HOSTNAME, command], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        return False


def sync_project() -> bool:
    """Sync project files to Raspberry Pi."""
    rsync_cmd = [
        "rsync",
        "-avz",
        "--delete",
        "--exclude",
        ".git",
        "--exclude",
        "__pycache__",
        "--exclude",
        "*.pyc",
        "--exclude",
        ".pytest_cache",
        MAC_PROJECT_PATH,
        f"{PI_HOSTNAME}:{PI_PROJECT_PATH}",
    ]
    print("Syncing project to Pi...")
    try:
        subprocess.run(rsync_cmd, check=True)
        print("✓ Project sync complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Project sync failed: {e}")
        return False


def install_system_dependencies() -> bool:
    """Install system-level dependencies (picamera2) on Raspberry Pi."""
    print("Installing system-level dependencies...")
    install_picamera2_cmd = "sudo apt update && sudo apt install -y python3-picamera2"
    print("Installing python3-picamera2 system-wide...")
    try:
        subprocess.run(["ssh", PI_HOSTNAME, install_picamera2_cmd], check=True)
        print("✓ System dependencies installation complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ System dependencies installation failed: {e}")
        return False


def first_setup() -> bool:
    """Perform first-time setup including system dependencies installation."""
    print("=== First-time Setup ===")
    print("This will install system-level dependencies that are required only once.")

    if not install_system_dependencies():
        return False

    print("✓ First-time setup complete!")
    return True


def run_command(command: str) -> bool:
    """Run a command using system Python on Raspberry Pi."""
    python_command = f"cd {PI_PROJECT_PATH} && python3 {command}"
    return run_ssh_command(python_command, f"Running command: {command}")


def set_permissions() -> bool:
    """Set appropriate file permissions."""
    chmod_cmd = f"chmod -R u+x {PI_PROJECT_PATH}src/ {PI_PROJECT_PATH}tests/ {PI_PROJECT_PATH}scripts/"
    return run_ssh_command(chmod_cmd, "Setting execute permissions")


def main() -> int:
    """Main deployment function."""
    parser = argparse.ArgumentParser(
        description="""Deployment script for petlog project to Raspberry Pi.

This script handles:
1. Syncing project files to Raspberry Pi
2. Installing system-level dependencies
3. Running optional commands

Usage:
    python scripts/deploy.py --first-setup  # First time setup
    python scripts/deploy.py                # Regular deployment
    python scripts/deploy.py --test-hw      # Run tests only
    python scripts/deploy.py --run CMD      # Deploy and run command""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--first-setup",
        action="store_true",
        help="Perform first-time setup including system-level dependencies (picamera2). Only needed once.",
    )
    parser.add_argument(
        "--test-hw", action="store_true", help="Run hardware tests after deployment"
    )
    parser.add_argument(
        "--run",
        metavar="CMD",
        type=str,
        help="Command to run on the Pi after deployment",
    )

    args = parser.parse_args()

    print("=== Petlog Deployment to Raspberry Pi ===")

    # Step 1: First-time setup if requested
    if args.first_setup:
        if not first_setup():
            return 1

    # Step 2: Sync project files
    if not sync_project():
        return 1

    # Step 3: Set file permissions
    # if not set_permissions():
    #     return 1

    # Step 4: Run hardware tests if requested
    if args.test_hw:
        print("Running hardware tests...")
        if not run_command("tests/HW/test_camera.py"):
            print("❌ Hardware tests failed!")
            return 1
        print("✓ Hardware tests passed!")

    # Step 5: Run custom command if provided
    if args.run:
        print(f"Running command on Pi: {args.run}")
        subprocess.run(["ssh", PI_HOSTNAME, args.run], check=True)
        print("Remote command complete.")

    print("🎉 Deployment completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
