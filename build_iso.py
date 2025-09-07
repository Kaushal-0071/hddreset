import pycdlib
import os
import sys

def create_bootable_iso():
    """
    Assembles the files from the 'iso_root' directory into a bootable ISO.
    """
    iso_output_file = 'secure_wiper.iso'
    source_dir = 'iso_root'

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    iso = pycdlib.PyCdlib()

    iso.new(
        interchange_level=3,
        joliet=True,
        rock_ridge='1.09',
        vol_ident='SECURE_WIPER_V1'
    )

    print(f"Adding files from '{source_dir}' to the ISO...")

    for root, dirs, files in os.walk(source_dir):
        # NEW: In-place modification to exclude hidden directories from the walk
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        rel_path = os.path.relpath(root, source_dir)
        iso_path = '/' + rel_path.replace('\\', '/')
        if iso_path == '/.':
            iso_path = '/'

        for d in dirs:
            iso_compliant_path = os.path.join(iso_path, d).upper()
            iso.add_directory(iso_compliant_path, rr_name=d)
        
        for f in files:
            # NEW: Explicitly skip any hidden files
            if f.startswith('.'):
                print(f"  - Skipping hidden file: {os.path.join(root, f)}")
                continue

            local_file_path = os.path.join(root, f)
            iso_compliant_path = os.path.join(iso_path, f).upper()
            iso.add_file(local_file_path, iso_compliant_path, rr_name=f)
            print(f"  - Added {local_file_path}")

    # Add the El Torito boot information
    print("Making the ISO bootable...")
    boot_image = '/BOOT/ISOLINUX/ISOLINUX.BIN'
    boot_catalog = '/BOOT/ISOLINUX/BOOT.CAT'
    
    iso.add_eltorito(
        boot_image,
        boot_catalog,
        boot_load_size=4,
      
    )

    # Write the final ISO file
    print(f"Writing ISO to '{iso_output_file}'...")
   
    iso.write(iso_output_file)

    iso.close()
    print("\nSuccess! Bootable ISO created at:", iso_output_file)

if __name__ == "__main__":
    create_bootable_iso()