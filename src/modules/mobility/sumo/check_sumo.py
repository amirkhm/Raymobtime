import os
import logging
from pathlib import Path
from src.scripts.helpers import format_run_name

def check_sumo_simulation_status(c):
    runs = c.rmt.sampling_parameters[1]
    check = 0
    for run in range(runs):
        arquivo = Path(
            os.path.join(
                c.results_dir, 
                format_run_name(run), 
                'sumoOutputInfoFileName.txt'))
        if arquivo.exists():
            check += 1
        else:
            logging.warning(
                '\033[35m'
                f"[SUMO check] Satatus: Incomplete, there is no sumoOutputInfoFileName.txt at run {format_run_name(run)}."
                '\033[0m')
            break
    logging.info(
        '\033[92m'
        f"[SUMO check] Status: {check}/{runs} complete."
        '\033[0m')
    return check == runs