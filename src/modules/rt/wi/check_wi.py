import os
from pathlib import Path
from src.scripts.helpers import format_run_name
import logging

def check_wi_run_status(c):
    runs = c.rmt.sampling_parameters[1]
    check = 0
    for run in range(runs):
        file = Path(
            os.path.join(
                c.results_dir, 
                format_run_name(run), 
                c.insite_study_area_name,
                'status',
                'runstatus.complete'))
        if file.exists():
            check += 1
        else:
            logging.warning(
                '\033[35m'
                f"[Ray tracing check] Satatus: Incomplete, {format_run_name(run)} not completed."
                '\033[0m')
            break
    logging.info(
        '\033[92m'
        f"[Ray tracing check] Status: {check}/{runs} complete."
        '\033[0m')
    return check == runs
        