import os
import logging
from pathlib import Path

def check_sql_exists(c):
    arquivo = Path(
        os.path.join(
            c.result_dir_processed_data,
            c.base_config.output_name+'.db'))
    if arquivo.exists():
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
    arquivo = Path(
        os.path.join(
            c.result_dir_processed_data,
            'CoordVehicleTxRx.csv'))
    if arquivo.exists():
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
        