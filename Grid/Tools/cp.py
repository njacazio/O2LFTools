#!/usr/bin/env python3
import os
import subprocess
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging

## define global variables to be saved in the main
logger = logging.getLogger(__name__)

def configure_logging(args):
    if args.log:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("run.log")])
        
def execute_script(path, args, pbar=None, lock=None):
    # /alice/data/2023/LHC23zx/543442/cpass0/2220/o2_ctf_run00543442_orbit0120946752_tf0000000958_epn028/001/AO2D.root
    original_path = path
    period = original_path.split("/alice/data/2023/")[-1].split("/")[0]
    run_number = original_path.split("/alice/data/2023/")[-1].split("/")[1]
    misc = original_path.split("o2_ctf_")[-1].split("/")[0]
    target = f"{period}/{run_number}/{misc}.root"
    # Check if the folder exists
    if not os.path.exists(f'./{period}/{run_number}'):
        logger.info(f"Creating folder {period}/{run_number}")
        os.makedirs(f'./{period}/{run_number}')
    # Copy the file
    logger.info(f"Copying file {original_path} to {target}")
    result = subprocess.run(['alien_cp', f"alien://{original_path}", f'file://{target}'], check=True, stdout=subprocess.DEVNULL)
    # Update progress
    if pbar:
        with lock:
            pbar.update(1)
    return result

def get_list_of_files(path, pattern, min, max):
    # Get the list of files in the parent folder
    list = subprocess.run(["alien.py","find", path, pattern], stdout=subprocess.PIPE).stdout.splitlines()
    # convert the list to string
    list = [x.decode('utf-8') for x in list]
    # exclude the item based on the run number
    if min != -1:
        list = [x for x in list if int(x.split("/alice/data/2023/")[-1].split("/")[1]) >= min]
    if max != -1:
        list = [x for x in list if int(x.split("/alice/data/2023/")[-1].split("/")[1]) <= max]
    return list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alien file copy script",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('parent_folder',metavar="parent_folder", help='Full Alien path to the parent folder. (eg. /alice/data/2023/LHC23zx/)')
    parser.add_argument('--pattern', default="AO2D.root", help='Pattern to search for in the parent folder. (AO2D.root or AnalysisResults.root)')
    parser.add_argument('--multi_core', default=1, type=int, help='Number of cores to use for multiprocessing. (eg. 4)')
    parser.add_argument('--test', action='store_true', help='Enable test mode. Only process the first N files.')
    parser.add_argument('--minrun', default=-1, type=int, help='Minimum run number to process. (eg. 543437)')
    parser.add_argument('--maxrun', default=-1, type=int, help='Minimum run number to process. (eg. 543442)')
    parser.add_argument('--log', action='store_true', help='Enable logging to file.')
    args = parser.parse_args()

    configure_logging(args)
    run_list = get_list_of_files(args.parent_folder, args.pattern, args.minrun, args.maxrun)
    if args.test:
        run_list = run_list[:args.multi_core]
    logger.info(f"Found {len(run_list)} files to process.")
    
    # Thread-safe progress bar
    lock = threading.Lock()
    pbar = tqdm(total=len(run_list), desc="Processing files", dynamic_ncols=True, position=0)

    with ThreadPoolExecutor(max_workers=args.multi_core) as executor:
        # Submit all tasks for execution
        futures = [executor.submit(execute_script, run, args, pbar, lock) for run in run_list]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error occurred: {e}")