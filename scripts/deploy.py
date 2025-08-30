#!/usr/bin/env python3

import argparse
import subprocess
import sys

# --- CONFIGURATION ---
MAC_PROJECT_PATH = "/Users/albertocutone/local/projects/petlog/"
SERVER_USER = "metal"
SERVER_HOST = "192.168.1.74"
SERVER_PROJECT_PATH = "/home/metal/projects/petlog/"
SERVER_HOSTNAME = f"{SERVER_USER}@{SERVER_HOST}"


def run_ssh_command(command: str, description: str) -> bool:
    """Run a command on the Raspberry Pi via SSH."""
    print(f"{description}...")
    try:
        result = subprocess.run(["ssh", SERVER_HOSTNAME, command], check=True)
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
        f"{SERVER_HOSTNAME}:{SERVER_PROJECT_PATH}",
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
        subprocess.run(["ssh", SERVER_HOSTNAME, install_picamera2_cmd], check=True)
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
    python_command = f"cd {SERVER_PROJECT_PATH} && python3 {command}"
    return run_ssh_command(python_command, f"Running command: {command}")


def set_permissions() -> bool:
    """Set appropriate file permissions."""
    chmod_cmd = f"chmod -R u+x {SERVER_PROJECT_PATH}src/ {SERVER_PROJECT_PATH}tests/ {SERVER_PROJECT_PATH}scripts/"
    return run_ssh_command(chmod_cmd, "Setting execute permissions")


def run_tests() -> bool:
    """Run all tests on Raspberry Pi."""
    print("Running all tests on Raspberry Pi...")

    # Run library tests first (PyTorch and YOLO imports)
    print("Running library tests...")
    pytorch_test_cmd = f"cd {SERVER_PROJECT_PATH} && python3 -m unittest tests.lib.pytorch_test"
    if not run_ssh_command(pytorch_test_cmd, "Running PyTorch import test"):
        print("❌ PyTorch import test failed!")
        return False
    
    yolo_test_cmd = f"cd {SERVER_PROJECT_PATH} && python3 -m unittest tests.lib.yolo_test"
    if not run_ssh_command(yolo_test_cmd, "Running YOLO import test"):
        print("❌ YOLO import test failed!")
        return False
    
    # Run API tests
    # print("Running API tests...")
    # api_test_cmd = f"cd {SERVER_PROJECT_PATH} && python3 -m pytest tests/test_api.py -v"
    # if not run_ssh_command(api_test_cmd, "Running API tests"):
    #     print("❌ API tests failed!")
    #     return False

    # Run database tests
    print("Running database tests...")
    db_test_cmd = (
        f"cd {SERVER_PROJECT_PATH} && python3 -m pytest tests/test_database.py -v"
    )
    if not run_ssh_command(db_test_cmd, "Running database tests"):
        print("❌ Database tests failed!")
        return False

    print("✓ All tests passed!")
    return True


def start_fastapi_server() -> bool:
    """Start the FastAPI server on Raspberry Pi."""
    print("Starting FastAPI server...")
    server_command = f"cd {SERVER_PROJECT_PATH} && python3 src/main.py"
    print(f"Running: {server_command}")
    print(f"Web dashboard will be available at: http://{SERVER_HOST}:8000")
    print("Press Ctrl+C to stop the server")

    try:
        # Use subprocess.run without check=True to allow Ctrl+C interruption
        subprocess.run(["ssh", SERVER_HOSTNAME, server_command])
        return True
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False


def main() -> int:
    """Main deployment function."""
    parser = argparse.ArgumentParser(
        description="""Deployment script for petlog project to Raspberry Pi.

This script handles:
1. Running tests before deployment
2. Syncing project files to Raspberry Pi
3. Installing system-level dependencies
4. Starting the FastAPI server with web dashboard

Usage:
    python scripts/deploy.py --first-setup  # First time setup
    python scripts/deploy.py                # Regular deployment with tests
    python scripts/deploy.py --test-hw      # Run hardware tests after deployment
    python scripts/deploy.py --run          # Deploy, test, and start FastAPI server with dashboard""",
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
        action="store_true",
        help="Start FastAPI server with web dashboard on Pi after deployment",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip running tests before deployment",
    )

    args = parser.parse_args()

    print("=== Petlog Deployment to Raspberry Pi ===")

    # Step 1: First-time setup if requested
    if args.first_setup:
        if not first_setup():
            return 1

    # Step 2: Sync project files first
    if not sync_project():
        return 1

    # Step 3: Run tests after syncing unless --no-test is specified
    if not args.no_test:
        if not run_tests():
            print("❌ Deployment aborted due to test failures!")
            return 1

    # Step 4: Set file permissions
    # if not set_permissions():
    #     return 1

    # Step 5: Run hardware tests if requested
    if args.test_hw:
        print("Running hardware tests...")
        if not run_command("tests/HW/test_camera.py"):
            print("❌ Hardware tests failed!")
            return 1
        print("✓ Hardware tests passed!")

    # Step 6: Start FastAPI server with web dashboard if requested
    if args.run:
        if not start_fastapi_server():
            return 1

    print("🎉 Deployment completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
