import config as c
import argparse
import os
import shutil
import subprocess
import gc
import psutil
import os
import signal
from multiprocessing import Process

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
            cmd = [blensor_runfile, blensor_scenario_path, '--background', '-P', blend_runpy, '--', f'{i}']
            
            print(cmd)
            print(RED + f'Simulation n° {i}' + RESET)

            p = Process(target=run_blensor_safely, args=(cmd,))
            p.start()
            p.join(timeout=3700)  # Slightly longer than subprocess timeout
            if p.is_alive():
                p.terminate()
            
            print(RED + f'Memory after: {psutil.virtual_memory().used/1024/1024:.2f} MB' + RESET)
            
        gc.collect()

def run_blensor_safely(cmd):
    """Run Blensor in a fully isolated process"""
    # Create new process group for complete cleanup
    os.setpgrp()
    
    try:
        # Run with fresh environment
        env = os.environ.copy()
        env['BLENDER_USER_SCRIPTS'] = '/tmp'  # Isolate configs
        
        proc = subprocess.Popen(
            cmd,
            env=env,
            preexec_fn=os.setsid  # New session
        )
        proc.wait(timeout=3600)  # Timeout after 1 hour
        
    finally:
        # Kill entire process tree
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass


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