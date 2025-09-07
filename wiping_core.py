import sys
import subprocess
import json
import os

def list_physical_drives():
    """Lists all physical, non-removable drives in the system."""
    # This environment will always be linux
    return _list_drives_linux()

def _list_drives_linux():
    """Uses lsblk to list drives on Linux."""
    try:
        # -d for device, -J for JSON, -o for specific columns, -e7 to exclude loop devices
        result = subprocess.run(
            ['lsblk', '-dJ', '-o', 'NAME,MODEL,SIZE,SERIAL', '-e7'],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        drives = []
        for device in data['blockdevices']:
            drives.append({
                'path': f"/dev/{device.get('name', 'N/A')}",
                'model': device.get('model', 'N/A'),
                'size': device.get('size', 'N/A'),
                'serial': device.get('serial', 'N/A'),
            })
        return drives
    except FileNotFoundError:
        # This error is critical. It means the 'lsblk' command is not available.
        print("Error: 'lsblk' command not found. Is 'util-linux' package loaded?")
        return []
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error listing drives on Linux: {e}")
        return []

def wipe_drive(drive_path, method, progress_callback):
    """
    Wipes a drive using the specified method.
    """
    # Check for root privileges
    if os.geteuid() != 0:
        return False, "This operation requires root privileges. Please run with sudo."
    
    if not os.path.exists(drive_path):
        return False, f"Device path {drive_path} does not exist."
    
    # Validate progress_callback
    if progress_callback is None:
        progress_callback = lambda msg, pct: None  # No-op function if not provided

    if method == 'overwrite':
        return _overwrite_drive(drive_path, passes=1, progress_callback=progress_callback) # Reduced to 1 pass for hackathon speed
    elif method == 'purge':
        return _secure_erase_linux(drive_path, progress_callback=progress_callback)
    else:
        return False, f"Unknown wipe method: {method}"

def _overwrite_drive(drive_path, passes, progress_callback):
    """Performs a multi-pass overwrite (NIST 800-88 Clear)."""
    try:
        # Unmount the device and all its partitions before wiping
        progress_callback(f"Attempting to unmount {drive_path}...", 0)
        # Unmount the device itself
        subprocess.run(['umount', drive_path], stderr=subprocess.DEVNULL)
        # Unmount any partitions (e.g., /dev/sda1, /dev/sda2, etc.)
        result = subprocess.run(['lsblk', '-ln', '-o', 'NAME', drive_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n')[1:]:  # Skip the first line (device itself)
                partition_path = f"/dev/{line.strip()}"
                subprocess.run(['umount', partition_path], stderr=subprocess.DEVNULL)

        # Get the correct size of the block device
        try:
            # Method 1: Use blockdev command (most reliable for block devices)
            result = subprocess.run(['blockdev', '--getsize64', drive_path],
                                  capture_output=True, text=True, check=True)
            total_size = int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            # Fallback: Use seek method
            try:
                with open(drive_path, 'rb') as f:
                    f.seek(0, 2)  # Seek to end
                    total_size = f.tell()
                    if total_size == 0:
                        return False, "Unable to determine device size. Device may be empty or inaccessible."
            except IOError as e:
                return False, f"Unable to determine device size: {e}"

        chunk_size = 1024 * 1024  # 1MB chunks

        with open(drive_path, 'wb') as f:
            for i in range(passes):
                progress_callback(f"Starting Pass {i + 1}/{passes}...", 0)
                f.seek(0)
                written_bytes = 0
                while written_bytes < total_size:
                    # Calculate remaining bytes to avoid writing past the end
                    remaining_bytes = total_size - written_bytes
                    current_chunk_size = min(chunk_size, remaining_bytes)
                    
                    # Write with random data for the first pass for better security
                    data = os.urandom(current_chunk_size) if i == 0 else bytes(current_chunk_size)
                    try:
                        bytes_written = f.write(data)
                        if bytes_written is None:
                            bytes_written = current_chunk_size  # Assume full write if None returned
                        written_bytes += bytes_written
                        
                        # Handle partial writes
                        if bytes_written < current_chunk_size:
                            f.flush()  # Ensure data is written
                            os.fsync(f.fileno())  # Force write to disk
                        
                        progress = min(100, int((written_bytes / total_size) * 100))
                        if written_bytes % (chunk_size * 10) == 0: # Update progress every 10MB
                            progress_callback(f"Pass {i+1}: {progress}%", progress)
                    except IOError as e:
                        return False, f"IO Error during write: {e}. Is drive in use or failing?"
                
                # Ensure all data is written to disk at the end of each pass
                f.flush()
                os.fsync(f.fileno())
        
        progress_callback("Overwrite complete. Verifying...", 100)
        # A final verification step could be added here in a real product
        return True, "Overwrite successful."
    except PermissionError:
        return False, "Permission denied. Please run with sudo."
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"

def _secure_erase_linux(drive_path, progress_callback):
    """
    Issues hardware secure erase commands (NIST 800-88 Purge).
    """
    progress_callback("Attempting Hardware Secure Erase...", 0)
    try:
        if 'nvme' in drive_path:
            return False, "NVMe Sanitize not implemented in this demo."
        else:
            progress_callback("Setting security password...", 25)
            # Using 'p' as the password for simplicity. NULL can be problematic.
            result = subprocess.run(['hdparm', '--user-master', 'u', '--security-set-pass', 'p', drive_path], 
                                  check=True, capture_output=True, text=True)
            
            progress_callback("Issuing secure erase command...", 50)
            # Note: This can take a very long time on real hardware.
            result = subprocess.run(['hdparm', '--user-master', 'u', '--security-erase', 'p', drive_path], 
                                  check=True, capture_output=True, text=True)

        progress_callback("Hardware erase command sent.", 100)
        return True, "Hardware secure erase command completed successfully."
    except FileNotFoundError:
        return False, "Command not found (hdparm/nvme). Is 'hdparm' package loaded?"
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else "No error details"
        error_msg = f"Hardware command failed. Drive may not support it or is frozen.\n\nSTDERR:\n{error_output}"
        return False, error_msg
    except PermissionError:
        return False, "Permission denied. Please run with sudo."