import os
import numpy as np
import yaml
from pathlib import Path
from types import SimpleNamespace
import logging
#logging.basicConfig(level=logging.DEBUG)

# simulators
from src.modules.blensor.blensor_src import blensor_simulation
from src.modules.rt.wi.simulation.simulation import main as simulation_main
from src.modules.postprocessing import (
    gen_database,
    gen_csv_file, 
    gen_rays_dataset, 
    gen_beam_output_file,
   gen_lidar_matrix,
   image_refinement,
   sanity_check_up)

def dict_to_namespace(obj):
    if isinstance(obj, dict):
        return SimpleNamespace(**{
            key: dict_to_namespace(value)
            for key, value in obj.items()
        })

    if isinstance(obj, list):
        return [dict_to_namespace(item) for item in obj]

    return obj


def load_yaml(path):
    path = Path(path)

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data or {}


def deep_merge(default_dict, user_dict):
    result = default_dict.copy()

    for key, user_value in user_dict.items():
        default_value = result.get(key)

        if isinstance(default_value, dict) and isinstance(user_value, dict):
            result[key] = deep_merge(default_value, user_value)
        else:
            result[key] = user_value

    return result


def find_project_root():
    """
    Find the project root by looking for pyproject.toml.
    """
    current = Path(__file__).resolve()

    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent

    raise FileNotFoundError("Project root not found. pyproject.toml is missing.")


def load_config():
    """
    Load default.yaml and the user config.yaml from the project root.
    """

    project_root = find_project_root()

    default_path = project_root / "src" / "configs" / "default.yaml"

    user_path = project_root / "config.yaml"
    if not user_path.exists():
        user_path = project_root / "config.yml"

    if not default_path.exists():
        raise FileNotFoundError(
            f"File default.yaml not found at: {default_path}"
        )

    if not user_path.exists():
        raise FileNotFoundError(
            f"File config.yaml or config.yml not found at: {project_root}"
        )

    default_cfg = load_yaml(default_path)
    user_cfg = load_yaml(user_path)

    merged_cfg = deep_merge(default_cfg, user_cfg)

    return dict_to_namespace(merged_cfg)

def get_lat_long(base_insite_project_path):
    """
    Extract latitude and longitude from the base.txrx file of a Wireless InSite project.
    Args:       base_insite_project_path (str): Path to the base InSite project directory.
    Returns:    tuple[str, str]: A tuple containing (latitude, longitude) as strings.
    Raises:     FileNotFoundError: If the base.txrx file does not exist.
    """
    txrx_file = open(os.path.join(base_insite_project_path, 'base.txrx'), 'r')
    latitude = False
    longitude = False

    for line in txrx_file:
        if 'latitude' in line:
            latitude = line.split(' ')[1].replace('\n', '')
        if 'longitude' in line:
            longitude = line.split(' ')[1].replace('\n', '')
        if latitude and longitude:
            return latitude, longitude

def get_insite_version(base_insite_project_path):
    """
    Parse and return the Wireless InSite version from the model.study.xml file.
    Args:       base_insite_project_path (str): Path to the base InSite project directory.
    Returns:    str: The InSite version (e.g., '3.0', '3.2').
    Raises:     FileNotFoundError: If the model.study.xml file does not exist.
    """
    model_file = open(os.path.join(base_insite_project_path, 'model.study.xml'), 'r')
    insite_version = False
    for line in model_file:
        if '<InSite version="' in line:
            insite_version = line.split('version=')[1].split(' ')[0][1:4]
            model_file.close()
            return insite_version

class parameters:
    def __init__(self):
        self.cfg = load_config()

        self.base_config = self.cfg.base_config
        self.pipeline = self.cfg.pipeline
        self.rmt = self.cfg.rmt
        self.sumo = self.cfg.sumo
        self.ray_tracing = self.cfg.ray_tracing
        self.blensor_options = self.cfg.blensor_options
        self.post_processing = self.cfg.post_processing

        self.setparameters()

    def setparameters(self):
        self.working_directory = find_project_root()
        #os.path.dirname(os.path.realpath(__file__))

        self.fixed_receivers = self.rmt.features.fixed_receivers
        self.vehicles_template = self.rmt.features.vehicles_template
        self.isolated_sim = not self.rmt.enabled
        
        self.use_pedestrians = self.ray_tracing.use_pedestrians
        self.drone_simulation = self.ray_tracing.use_drone
        self.V2V = self.ray_tracing.v2v.enable
        
        self.base_insite_project_path = os.path.join(
            self.working_directory,
            "data",                                
            self.base_config.scenario,
            "base",
            "wi" #It's possible differents base InSite projects, add in yaml
        ) 

        # Folder to store each InSite project and its results
        # Will create subfolders for each "run", run0000, run0001, etc.
        self.results_dir = os.path.join(
            self.working_directory,
            'data',
            self.base_config.scenario,
            'out',
            self.base_config.output_name,
            'rt_simulations')
        
        self.results_dir_postprocessed = os.path.join(
            self.working_directory,
            'data',
            self.base_config.scenario,
            'out',
            self.base_config.output_name,
            'processed_data')

        self.resume = self.base_config.resume
        self.clean_previous = self.base_config.clean_previous 
        
        self.isolated_results_dir = os.path.join(
            self.results_dir,
            self.base_config.scenario)

        # Folders and files for InSite and its license.
        # For Windows you may simply inform the path to the executable files,
        # not minding about the license file location.
        # Folders for SUMO and InSite.
        # Use executable sumo-gui if want to see the GUI or sumo otherwise.
        self.insite_version = get_insite_version(self.base_insite_project_path)

        # InSite env variable
        self.locale = 'LC_CTYPE=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8 LC_TIME=en_US.UTF-8 '

        if self.insite_version == '3.3':
            self.wibatch_bin = (
                self.locale
                + '{} '.format(self.ray_tracing.wireless_insite.LICENSE_FILE)
                + 'LD_LIBRARY_PATH={}/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ '.format(
                    self.ray_tracing.wireless_insite.software_path)
                + '{}/WirelessInSite/3.3.0.4/Linux-x86_64RHEL6/bin/wibatch'.format(
                    self.ray_tracing.wireless_insite.software_path))

        elif self.insite_version == '3.2':
            self.wibatch_bin = (
                self.locale
                + f"{self.ray_tracing.wireless_insite.LICENSE_FILE} "
                + f"LD_LIBRARY_PATH={self.ray_tracing.wireless_insite.software_path}/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ "
                + f"{self.ray_tracing.wireless_insite.software_path}/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/wibatch")

        if not self.isolated_sim:
            self.sumo_bin = self.sumo.bin
            self.sumo_cfg = os.path.join(
                self.working_directory,
                'data',
                self.base_config.scenario,
                'base',
                'sumo',
                f'{self.sumo.cfg}.sumocfg')

            # Iterator that determines maximum number of RT simulations
            self.n_run = range(
                self.rmt.sampling_parameters[0],
                self.rmt.sampling_parameters[1])

            # Time interval between scenes, in seconds
            self.sampling_interval = float(self.rmt.sampling_parameters[2])

            # Number of scenes of each episode
            self.scenes_per_episode = int(self.rmt.scenes_per_episode)

            # Time among episodes, in steps
            # If you specify x/Ts, then x is in seconds
            self.time_between_episodes = int(
                float(self.rmt.time_between_episodes) / self.sampling_interval)

        if self.fixed_receivers:
            # Number of receivers per episode
            self.receivers_per_episode = 0
        else:
            # Number of receivers per episode
            self.receivers_per_episode = self.ray_tracing.receivers_per_episode

        self.analysis_area_enabled = self.post_processing.area_of_analyses.enabled
        self.analysis_area = self.post_processing.area_of_analyses.limits
        self.analysis_area_resolution = 0.5

        self.antenna_number = 10 #VERIFY

        # Frequency in Hz for the RT simulation
        self.frequency = 60e9

        self.set_area_limit = self.pipeline.mobility.placement_limits.enabled
        self.max_lim = self.pipeline.mobility.placement_limits.max_lim
        self.min_lim = self.pipeline.mobility.placement_limits.min_lim

        # Blender Options
        self.sim_BS_img = self.blensor_options.image_options.BS_camera
        self.sim_UE_img = self.blensor_options.image_options.UE_camera
        self.n_cameras_blensor_scenario = self.blensor_options.image_options.n_camera_BS

        self.blensor_scenario_path = self.blensor_options.path_to_scenario_blend
        self.blensor_runfile_path = self.blensor_options.path_blensor_image
        self.path_to_vehicles_blend = self.blensor_options.path_to_vehicles_blend  

        self.CoordSystem = self.post_processing.cartesian_lidar_matrix.coordinate_system
        self.QP = self.post_processing.cartesian_lidar_matrix.QP
        self.QPsph = self.post_processing.cartesian_lidar_matrix.QPsph
        self.Tx_position = self.post_processing.cartesian_lidar_matrix.Tx_position
        self.max_dist_LIDAR = self.post_processing.cartesian_lidar_matrix.max_dist_LIDAR
        self.type_data = self.post_processing.cartesian_lidar_matrix.type_data

        if self.V2V:
            self.n_Tx_per_episode = self.ray_tracing.transmitters_per_episode
            self.receivers_per_episode = self.ray_tracing.receivers_per_episode
            self.close_vehicles = self.ray_tracing.v2v.close_vehicles
            self.n_of_vehicles = self.ray_tracing.v2v.n_of_vehicles
            if self.ray_tracing.v2v.chose_vehicle:
                self.chosen_vehicle = self.ray_tracing.v2v.chosen_vehicle

        self.import_precoding = self.post_processing.mimo.import_precoding
        self.import_hmatrix = self.post_processing.mimo.import_channels
        self.import_combining = self.post_processing.mimo.import_combining
        self.expansion = self.post_processing.mimo.antenna_array_expansion
        self.rotation = self.post_processing.mimo.array_rotation
        self.normalized_antenna_distance = self.post_processing.mimo.antenna_array_expansion.normalized_antenna_distance


        # Fullfill this parameters with InSite's information
        self.insite_study_area_name = self.ray_tracing.wireless_insite.base_files_names.study_area_name
        self.insite_tx_name = self.ray_tracing.wireless_insite.base_files_names.tx_name
        self.insite_rx_name = self.ray_tracing.wireless_insite.base_files_names.rx_name
        self.insite_setup_name = self.ray_tracing.wireless_insite.base_files_names.setup_name
        self.insite_vehicles_name = self.ray_tracing.wireless_insite.base_files_names.vehicles_name

        if self.vehicles_template:
            self.latitude, self.longitude = get_lat_long(self.base_insite_project_path)
            self.insite_vehicles_name_model = self.insite_vehicles_name
            self.insite_vehicles_name = self.insite_vehicles_name + '_'


        if self.isolated_sim:
            self.results_base_model_dir = self.isolated_results_dir
        else:
            self.results_base_model_dir = os.path.join(self.results_dir, 'base')

        self.results_base_model_dir.replace('\\', '/')
        # Input files, which are read by the Python scripts

        # File that has the base InSite project
        self.setup_path = os.path.join(self.base_insite_project_path, self.insite_setup_name + '.setup')
        self.base_setup_path = os.path.join(self.base_insite_project_path, 'base.setup')

        # setup_path = setup_path.replace(' ', '\ ') # deal with paths with blank spaces

        # XML that has information about the simulations
        self.base_x3d_xml_path = os.path.join(
            self.base_insite_project_path,
            'base.' + self.insite_study_area_name + '.xml')

        # Name, basename, of the paths file generated in the simulation
        self.paths_file_name = self.insite_setup_name + '.paths.t001_01.r002.p2m'

        # Base object file to generate the object_dst_file_name
        self.base_object_file_name = os.path.join(
            self.base_insite_project_path, 
            "base.object")

        # Base txrx file to generate the txrx_dst_file_name
        self.base_txrx_file_name = os.path.join(
            self.base_insite_project_path, 
            "base.txrx")


        # Output files, which are written by the Python scripts.
        # Provide here only the names.
        # The full paths will be created by simulation.py, using the run folder.

        # Name, basename, of the JSON output simulation info file
        self.simulation_info_file_name = 'wri-simulation.info'

        self.dst_object_file_name = self.insite_vehicles_name + '.object'
        self.dst_txrx_file_name = self.insite_setup_name + '.txrx'

        # XML project that will be executed by InSite command line tools
        # Its path will be the run folder.
        self.dst_x3d_xml_file_name = (
            self.insite_setup_name
            + '.'
            + self.insite_study_area_name
            + '.xml')

        # The information below is added in simulation.py into an XML file
        if self.insite_version == '3.3':
            self.dst_x3d_txrx_xpath = (
                "./remcom__rxapi__Job/Scene/remcom__rxapi__Scene/TxRxSetList/"
                "remcom__rxapi__TxRxSetList/TxRxSet/remcom__rxapi__PointSet/"
                "OutputID/remcom__rxapi__Integer[@Value='2']"
                + "/../../ControlPoints/remcom__rxapi__ProjectedPointList")
            self.dst_x3d_txrx_xpath_to_tx = (
                "./remcom__rxapi__Job/Scene/remcom__rxapi__Scene/TxRxSetList/"
                "remcom__rxapi__TxRxSetList/TxRxSet/remcom__rxapi__PointSet/"
                "OutputID/remcom__rxapi__Integer[@Value='1']"
                + "/../../ControlPoints/remcom__rxapi__ProjectedPointList")
        else:
            self.dst_x3d_txrx_xpath = (
                "./Job/Scene/Scene/TxRxSetList/TxRxSetList/TxRxSet/"
                "PointSet/OutputID/Integer[@Value='2']"
                + "/../../ControlPoints/ProjectedPointList")
            self.dst_x3d_txrx_xpath_to_tx = (
                "./Job/Scene/Scene/TxRxSetList/TxRxSetList/TxRxSet/"
                "PointSet/OutputID/Integer[@Value='1']"
                + "/../../ControlPoints/ProjectedPointList")

        self.tool = self.pipeline.mobility.tool
        if self.isolated_sim:
            self.use_sumo = False
        else:
            self.use_sumo = True

        # Dimensions of the Mobile Objects, MOBJS, which will be placed on dst_object_file_name
        self.car_dimensions = (2, 6, 1.47)

        # Antenna to be placed above the cars
        self.antenna_origin = (
            self.car_dimensions[0] / 2,
            self.car_dimensions[1] / 2,
            self.car_dimensions[2])

        # ID of the car material.
        # Must be defined on base_object_file_name and it is processed by simulation.py.
        self.car_material_id = 0
        self.car_structure_name = 'car'

        # Name of the antenna points in base_txrx_file_name
        self.insite_rx_name = self.insite_rx_name


        if self.use_sumo:
            seed = self.sumo.seed
            np.random.seed(seed)

            self.sumo_cmd = [
                self.sumo.bin,
                '-c',
                self.sumo_cfg,
                '--step-length',
                str(self.sampling_interval),
                '--seed',
                '{}'.format(seed)]

            # Mapping from SUMO to InSite coordinates.
            # Take only min and max for x and y and put there.
            self.lane_boundary_dict = {
                "laneA_0": [[758.5, 460], [744.5, 660]],
                "laneB_0": [[658.82, 460], [747.5, 358.76]],
                "laneC_0": [[658.82, 460], [752.5, 675.90]],
                "laneD_0": [[840.08, 460], [755.5, 660]]}

        else:
            # Not sure if this is ancient code used for debugging with use_sumo = False.

            # Origin and destination of the line to place the cars
            self.line_origin = (
                (755.25, 470, 0.2),
                (755.25 + 5, 470, 0.2),)

            # Dimension line_destination is indicating to
            self.line_destination = 645
            self.line_dimension = 1

            #! Verificar como essa função vai ser acessada (def entro de objeto) e se é necessário colocar self ou não
            # Distance between cars
            def car_distances():
                return np.random.uniform(1.5, 6)
        
        self.mobility = self.pipeline.mobility
        self.ray_tracing = self.pipeline.ray_tracing
        self.jump = self.ray_tracing.jump
        self.post_processing = self.pipeline.post_processing
        self.blensor = self.pipeline.blensor
        self.validation = self.pipeline.validation
        

def raymobtime():
    """
    Raymobtime simulation and post-processing entry point.

    This function run the main Raymobtime workflow stages, including Wireless InSite ray-tracing simulation,
    Blensor-based LiDAR/image generation, and post-processing routines for database, coordinate,
    ray, beam, LiDAR, and image outputs.

    Depending on the selected inputs in, it can generate simulation input files,
    execute ray tracing, convert raw results into structured datasets, run sanity
    checks, or process auxiliary sensor data.
    """

    c = parameters()

    # Usual Raymobtime Simulation using WI
    if c.mobility.enabled or c.ray_tracing.enabled:
        simulation_main(c)

    # Simulation using blensor for image/lidar database
    if (c.blensor.enabled):
        blensor_simulation(c)

    postprocessing_modules = {
       "db": gen_database,
       "coord": gen_csv_file,
       "rays": gen_rays_dataset,
       "beams": gen_beam_output_file,
       "lidar": gen_lidar_matrix,
       "image": image_refinement,
    }

    if c.post_processing.enabled: 
       print("Starting post-processing...")
       if c.post_processing.which == "all":
           for func in [gen_database, gen_csv_file, gen_rays_dataset, gen_beam_output_file]:
               func(c)

       for output in c.post_processing.outputs:
           if output in postprocessing_modules:
               func = postprocessing_modules[output]
               func(c)
        
    # Saving the blensor simulation from pcd files to matrix type data
    CoordSystem = c.CoordSystem
    if (c.post_processing.enabled) and ("lidar" in c.post_processing.outputs):
       if CoordSystem.lower() == 'spherical' or CoordSystem.lower() == 'cartesian':
           gen_lidar_matrix(c)
       else:
           raise ValueError(f'CoordSystem {CoordSystem} not defined or value incorrect, use cartesian or spherical in config.yaml')
    elif (c.post_processing.enabled) and ("image" in c.post_processing.outputs):
       image_refinement(c)

    if c.validation.run_checkup:
       sanity_check_up(c)
    
if __name__ == "__main__":    
    raymobtime()
