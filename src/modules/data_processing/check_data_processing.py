import os
import pandas as pd
import logging
from pathlib import Path

def check_sql_exists(c):
    file = Path(
        os.path.join(
            c.result_dir_processed_data,
            c.base_config.output_name+'.db'))
    if file.exists():
        logging.info(
            '\033[92m'
            f"[SQL check] Status: complete."
            '\033[0m')
        return True
    else:
        logging.warning(
            '\033[35m'
            f"[SQL check] Satatus: Incomplete, no file found."
            '\033[0m')
        return False

def check_csv_exists(c):
    file = Path(
        os.path.join(
            c.result_dir_processed_data,
            'CoordVehicleTxRx.csv'))
    if file.exists():
        logging.info(
            '\033[92m'
            f"[CSV check] Status: complete."
            '\033[0m')
        return True
    else:
        logging.warning(
            '\033[35m'
            f"[CSV check] Satatus: Incomplete, no file found."
            '\033[0m')
        return False
        
def check_hdf5_exists(c):
    # open csv
    csv_path = Path(
        os.path.join(
            c.result_dir_processed_data,
            'CoordVehicleTxRx.csv'))
    # read how many eps
    csv = pd.read_csv(csv_path)
    n_episodes = csv['EpisodeID'].nunique()
    # check existence of hdf5 files
    check = 0
    for i in range(n_episodes):
        arquivo = Path(
            os.path.join(
                c.result_dir_processed_data,
                f'rays',
                f'rays_ep{i}.hdf5'))
        if arquivo.exists():
            check += 1
        else:
            logging.warning(
                '\033[35m'
                f"[hdf5 check] Satatus: Incomplete, there is no rays_ep{i}.hdf5 for episode {i}."
                '\033[0m')
            break
    logging.info(
        '\033[92m'
        f'[hdf5 check] Status: {check}/{n_episodes} complete.'
        '\033[0m')
    return check == n_episodes
