import config as c
import argparse
import os
import shutil

def blensor_simulation(sim_type):
    # Will simulate blensor multiple times
    # Get paths from config file
    blensor_scenario_path = c.blensor_scenario_path
    blensor_runfile = c.blensor_runfile_path
    
    if sim_type=='lidar':
        main_simulator_python_file = ['blensor/lidar_sim.py']
    elif sim_type=='image':
        main_simulator_python_file = []
        if c.sim_BS_img:
            main_simulator_python_file.append('blensor/img_bs_sim.py')
        if c.sim_UE_img:
            main_simulator_python_file.append('blensor/img_sim.py')
        

    # Customize color in the terminal
    RED = '\033[91m'
    RESET = '\033[0m'

    for i in range(min(c.n_run),max(c.n_run)+1):
        # if os.path.exists(f'scans/scans_run{i:05d}.zip') and lidar:
        #     continue
        print('Running command...')
        for blend_runpy in main_simulator_python_file:
            cmd = (
                f'{blensor_runfile} {blensor_scenario_path} --background -P {blend_runpy}'
            )
            
            print(cmd)
            print(RED + f'Simulation n° {i}' + RESET)
            os.system(cmd)

def export_cam_info():
    """
    Run terminal code to export camera blensor information from the Base Station
    """
    blensor_scenario_path = c.blensor_scenario_path
    blensor_runfile = c.blensor_runfile_path

    cmd = (f'{blensor_runfile} {blensor_scenario_path} --background -P blensor/data_extractor.py')
    os.system(cmd)

if __name__ == "__main__":
    blensor_simulation('lidar')