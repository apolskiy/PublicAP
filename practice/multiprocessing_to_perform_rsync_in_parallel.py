"""This script uses multiprocessing to perform rsync operations in parallel,
thus unloading CPU for backup tasks."""
#Aleksandr Polskiy script created to unload CPU for backup tasks
#!/usr/bin/env python3
import argparse
import subprocess
import os
from multiprocessing import Pool



#This function executes an rsync command for a single source item.
def rsync_worker(source_item, destination_base, rsync_opts):

    """Executes an rsync command for a single source item.

    """

    source_path = source_item

    destination_path = os.path.join(destination_base, os.path.basename(source_item))

    command = ["rsync",rsync_opts,source_path,destination_path]

    try:

        print(f"Executing command: {command} \n")
        subprocess.run(command, check=True)

        print(f"Successfully synced: {source_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error syncing {source_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Processes source and '
                                                 'destination directories for rsync.')
    parser.add_argument('-d','--dest',type=str, default="/data/prod/",
                        help='Destination directory')
    parser.add_argument('-s','--src', type=str,
                        default="/home/data/prod_backup/", help='Source directory')
    parser.add_argument('-p', '--parameters', type=str,
                        default="-arq", help='rsync parameters')

    args = parser.parse_args()
    src= args.src
    dest = args.dest
    rsync_options=args.parameters

    # Get a list of items to sync (e.g., subdirectories or files)

    items_to_sync = [os.path.join(src, item) for item in os.listdir(src)]



    num_processes = os.cpu_count() or 4  # Use all available CPU cores or a default

    #original rsync run without multiprocessing:
    #subprocess.call(["rsync", "-arq", src, dest])

    #multiprocessed rsync run as a pool
    with Pool(processes=num_processes) as pool:

        # Map the rsync_worker function to each item, passing destination and options

        pool.starmap(rsync_worker, [(item, dest, rsync_options) for item in items_to_sync])



    print("All rsync tasks completed.")
