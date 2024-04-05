import config as c
import os

def main(simulator, batch = 100):
    # Will simulate blensor multiple times
    # Get paths from config file
    runs = max(c.n_run)
    simulation_path = c.results_dir
    blensor_scenario_path = c.blensor_scenario_path
    end = blensor_scenario_path.split('/')[-1]
    vehicles_blend_path = blensor_scenario_path.replace(end, 'vehicles.blend')
    for i in range(min(c.n_run),max(c.n_run)+1):
        if os.path.exists(f'scans/scans_run{i:05d}.zip'):
            continue
        print('Running command...')
        print(f'Blensor {blensor_scenario_path} -P {simulator} --from_run {i} --to {i+1}')
        os.system(f'Blensor {blensor_scenario_path} --background -P {simulator} --from_run {i} --to {i+1} --simulation {simulation_path} --veh_path {vehicles_blend_path}')

if __name__ == "__main__":
    main('blensor/lidar_sim.py')