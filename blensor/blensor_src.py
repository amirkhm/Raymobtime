import config as c
import argparse
import os

def main(pysim, lidar=False, img=False):
    # Will simulate blensor multiple times
    # Get paths from config file
    runs = max(c.n_run)
    simulation_path = c.results_dir
    blensor_scenario_path = c.blensor_scenario_path
    end = blensor_scenario_path.split('/')[-1]
    vehicles_blend_path = blensor_scenario_path.replace(end, 'vehicles.blend')
    blensor_runfile = c.blensor_runfile_path

    # Customize color in the terminal
    RED = '\033[91m'
    RESET = '\033[0m'

    for i in range(min(c.n_run),max(c.n_run)+1):
        # if os.path.exists(f'scans/scans_run{i:05d}.zip') and lidar:
        #     continue
        print('Running command...')
        cmd = (
            f'{blensor_runfile} {blensor_scenario_path} --background -P {pysim}'
            f' --from_run {i} --to {i+1} --simulation {simulation_path} --veh_path {vehicles_blend_path}'
        )
        
        print(cmd)
        print(RED + f'Simulation n° {i}' + RESET)
        os.system(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--lidar', action='store_true',
                        help='Run lidar simmulation')
    parser.add_argument('-i', '--image', action='store_true',
                        help='Run Image simulation')
    args = parser.parse_args()

    if args.lidar:
        main_simulator_python_file = 'blensor/lidar_sim.py'
    elif args.image:
        main_simulator_python_file = 'blensor/img_sim.py'
    main(main_simulator_python_file, args.lidar, args.image)