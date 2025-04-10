import config as c
import argparse
import os
import shutil

def blensor_simulation(sim_type):
    # Will simulate blensor multiple times
    # Get paths from config file
    runs = max(c.n_run)
    simulation_path = c.results_dir
    blensor_scenario_path = c.blensor_scenario_path
    end = blensor_scenario_path.split('/')[-1]
    vehicles_blend_path = blensor_scenario_path.replace(end, 'vehicles.blend')
    blensor_runfile = c.blensor_runfile_path
    
    if sim_type=='lidar':
        main_simulator_python_file = 'blensor/lidar_sim.py'
    elif sim_type=='image':
        main_simulator_python_file = 'blensor/img_sim.py'

    if not os.path.exists('scans'):
        os.makedirs('scans')

    # Customize color in the terminal
    RED = '\033[91m'
    RESET = '\033[0m'

    for i in range(min(c.n_run),max(c.n_run)+1):
        # if os.path.exists(f'scans/scans_run{i:05d}.zip') and lidar:
        #     continue
        print('Running command...')
        cmd = (
            f'{blensor_runfile} {blensor_scenario_path} --background -P {main_simulator_python_file}'
            f' --from_run {i} --to {i+1} --simulation {simulation_path} --veh_path {vehicles_blend_path}'
        )
        
        print(cmd)
        print(RED + f'Simulation n° {i}' + RESET)
        os.system(cmd)
        
    new_scan_folder = os.path.join(c.working_directory, 'sim_data', c.sim_name, 'scans')
    if not os.path.exists(new_scan_folder):
        os.makedirs(new_scan_folder)

    for zip_file in os.listdir('scans'):
        src = os.path.join('scans', zip_file)
        dst = os.path.join(new_scan_folder, zip_file)
        shutil.move(src, dst)
        
    os.rmdir('scans')

if __name__ == "__main__":
    blensor_simulation('lidar')