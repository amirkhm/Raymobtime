import os
import pandas as pd
import logging
from pathlib import Path

def check_beams(c):
    beams_folder = Path(
        os.path.join(
            c.results_dir_postprocessed,
            'beams'))
    if beams_folder.exists():
        logging.info(
            '\033[92m'
            f"[Beams check] Status: complete."
            '\033[0m')
        return True
    else:
        logging.warning(
            '\033[35m'
            f"[Beams check] Satatus: Incomplete, no folder found."
            '\033[0m')
        return False
    
def check_refined_images(c):
    refined_images_folder = Path(
        os.path.join(
            c.results_dir_postprocessed,
            'refined_images'))
    if refined_images_folder.exists():
        logging.info(
            '\033[92m'
            f"[Refined images check] Status: complete."
            '\033[0m')
        return True
    else:
        logging.warning(
            '\033[35m'
            f"[Refined images check] Satatus: Incomplete, no folder found."
            '\033[0m')
        return False
    
def check_lidar_matrix(c):
    coord_type =  c.CoordSystem [:3]
    geometry_type = c.type_data
    lidar_matrix_folder = Path(
        os.path.join(
            c.results_dir_postprocessed,
            f'lidar_{coord_type}_matrix_{geometry_type}'))
    if lidar_matrix_folder.exists():
        logging.info(
            '\033[92m'
            f"[Lidar matrix check] Status: complete."
            '\033[0m')
        return True
    else:
        logging.warning(
            '\033[35m'
            f"[Lidar matrix check] Satatus: Incomplete, no folder found."
            '\033[0m')
        return False