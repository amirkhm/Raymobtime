import os
import logging
from src.scripts.helpers import format_run_name
from pathlib import Path

def check_blensor_images(c):
    if c.sim_BS_img:
        checkBS = 0
        runs = c.rmt.sampling_parameters[1]
        for run in range(runs):
            BS_images_path = Path(
                os.path.join(
                    c.result_dir_processed_data,
                    'images',
                    'BS',
                    f'run{run}'))
            if BS_images_path.exists():    
                checkBS += 1
            else:
                logging.warning(
                    '\033[35m'
                    f"[Blensor images check] BS Satatus: Incomplete, run{run}, files not found."
                    '\033[0m')
                break
        logging.info(
            '\033[92m'
            f"[Blensor images check] BS Status: {checkBS}/{runs} complete."
            '\033[0m')
        checkBS = 1 if checkBS == runs else 0

    if c.sim_UE_img:
        checkUE = 0
        runs = c.rmt.sampling_parameters[1]
        for run in range(runs):
            UE_images_path = Path(
                os.path.join(
                    c.result_dir_processed_data,
                    'images',
                    'UE',
                    f'run{run}'))
            if UE_images_path.exists():    
                checkUE += 1
            else:
                logging.warning(
                    '\033[35m'
                    f"[Blensor images check] UE Satatus: Incomplete, run{run}, files not found."
                    '\033[0m')
                break
        logging.info(
            '\033[92m'
            f"[Blensor images check] UE Status: {checkUE}/{runs} complete."
            '\033[0m')
        checkUE = 1 if checkUE == runs else 0
    return True if (checkBS and checkUE) else False
        

def check_blensor_lidar(c):
    runs = c.rmt.sampling_parameters[1]
    check = 0
    for run in range(runs):
        scan_run = Path(
            os.path.join(
                c.result_dir_processed_data,
                'scans',
                f'scans_{format_run_name(run)}.zip'))
        if scan_run.exists():
            check += 1
        else:
            logging.warning(
                '\033[35m'
                f"[blensor lidar check] Satatus: Incomplete, {format_run_name(run)} not completed."
                '\033[0m')
            break
    logging.info(
        '\033[92m'
        f"[Blensor lidar check] Status: {check}/{runs} complete."
        '\033[0m')
    return check == runs