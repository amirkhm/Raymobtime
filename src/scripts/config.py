import os
import numpy as np
import yaml
from pathlib import Path
from types import SimpleNamespace
import logging
logging.basicConfig(level=logging.DEBUG)


def dict_to_namespace(obj):
    """
    Converts dictionaries loaded from YAML into objects with dot access.nto.
    """
    if isinstance(obj, dict):
        return SimpleNamespace(**{
            key: dict_to_namespace(value)
            for key, value in obj.items()
        })
    elif isinstance(obj, list):
        return [dict_to_namespace(item) for item in obj]
    else:
        return obj


def load_config():
    """
    Loads the configuration from a YAML file (config.yaml or config.yml) and returns it as an object with access por ponto.
    """
    config_path = Path("config.yaml")

    if not config_path.exists():
        config_path = Path("config.yml")

    if not config_path.exists():
        raise FileNotFoundError(
            "File not found. "
            "Please create a config.yaml or config.yml file in the execution directory."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        cfg_dict = yaml.safe_load(f)

    if cfg_dict is None:
        raise ValueError(f"The file {config_path} is empty or invalid.")

    return dict_to_namespace(cfg_dict)


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

def base_run_dir_fn(i):
    """
    Returns the run_dir for run i.

    The folders will be:
        run00001
        run00002
        ...
    """
    return "run{:05d}".format(i)


cfg = load_config() # load yaml

working_directory = os.path.dirname(os.path.realpath(__file__))
base_insite_project_path = os.path.join(
    working_directory,
    'base_files',
    cfg.simulation_paths.base_insite_path)
results_dir = os.path.join(
    working_directory,
    'simulations',
    cfg.simulation_paths.results_dir_path)
isolated_results_dir = os.path.join(
    results_dir,
    cfg.simulation_paths.base_insite_path)
sim_name = cfg.simulation_paths.results_dir_path
isolated_sim = cfg.features.isolated_simulation
insite_version = get_insite_version(base_insite_project_path)
# InSite env variable
locale = 'LC_CTYPE=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8 LC_TIME=en_US.UTF-8 '


if insite_version == '3.3':
    wibatch_bin = (
        locale
        + f"{cfg.insite_paths.REMCOMINC_LICENSE_FILE} "
        + f"LD_LIBRARY_PATH={cfg.insite_paths.insite_software_path}/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ "
        + f"{cfg.insite_paths.insite_software_path}/WirelessInSite/3.3.0.4/Linux-x86_64RHEL6/bin/wibatch")
elif insite_version == '3.2':
    wibatch_bin = (
        locale
        + f"{cfg.insite_paths.REMCOMINC_LICENSE_FILE} "
        + f"LD_LIBRARY_PATH={cfg.insite_paths.insite_software_path}/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ "
        + f"{cfg.insite_paths.insite_software_path}/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/wibatch")

use_fixed_receivers = cfg.features.use_fixed_receivers
use_pedestrians = cfg.features.use_pedestrians
use_vehicles_template = cfg.features.use_vehicles_template
drone_simulation = cfg.features.drone_simulation
mimo_orientation = cfg.features.mimo_orientation
use_V2V = cfg.features.use_V2V

n_run = range(1)

if not isolated_sim:
    # SUMO configuration file
    sumo_bin = cfg.sumo_files.sumo_bin
    sumo_cfg = os.path.join(
        working_directory,
        'base_files',
        'sumo',
        '{}.sumocfg'.format(cfg.sumo_files.sumo_cfg)
    )

    # SUMO configuration file
    sumo_bin = cfg.sumo_files.sumo_bin
    sumo_cfg = os.path.join(
        working_directory,
        'base_files',
        'sumo',
        '{}.sumo.cfg'.format(cfg.sumo_files.sumo_cfg)
    )

    # Iterator that determines maximum number of RT simulations
    n_run = range(
        cfg.simulation_parameters.n_init_run,
        cfg.simulation_parameters.n_end_run)
    sampling_interval = float(cfg.simulation_parameters.sampling_interval)
    time_of_episode = int(cfg.simulation_parameters.n_scenes_of_each_episode)
    time_between_episodes = int(float(cfg.simulation_parameters.time_between_episodes) / sampling_interval)

n_antenna_per_episode = 0 if use_fixed_receivers else cfg.simulation_parameters.n_antenna_per_episode

if use_V2V:
    n_Tx_per_episode = cfg.simulation_parameters.n_Tx_per_episode
    n_antenna_per_episode = cfg.simulation_parameters.n_antenna_per_episode

analysis_area_enabled = cfg.data_handler.area_of_analyses.enabled
analysis_area = cfg.data_handler.area_of_analyses.coordinates_limits
set_area_limit = cfg.area_limits.enabled
max_lim = cfg.area_limits.max_lim
min_lim = cfg.area_limits.min_lim

# Blender Options
sim_BS_img = cfg.blensor_options.img_simulation_options.BS_camera
sim_UE_img = cfg.blensor_options.img_simulation_options.UE_camera
n_cameras_blensor_scenario = cfg.blensor_options.img_simulation_options.n_camera_BS

CoordSystem = cfg.data_handler.cartesian_lidar_matrix.coordinate_system
QP = cfg.data_handler.cartesian_lidar_matrix.QP
QPsph = cfg.data_handler.cartesian_lidar_matrix.QPsph
Tx_position = cfg.data_handler.cartesian_lidar_matrix.Tx_position
max_dist_LIDAR = cfg.data_handler.cartesian_lidar_matrix.max_dist_LIDAR
type_data = cfg.data_handler.cartesian_lidar_matrix.type_data

if use_V2V:
    close_vehicles = cfg.v2v_options.close_vehicles
    n_of_vehicles = cfg.v2v_options.n_of_vehicles
    chosen_vehicle = cfg.v2v_options.chosen_vehicle

import_precoding = cfg.data_handler.antenna_arr.import_precoding
import_hmatrix = cfg.data_handler.antenna_arr.import_hmatrix
import_combining = cfg.data_handler.antenna_arr.import_combining
expansion = cfg.data_handler.antenna_arr.expansion
rotation = cfg.data_handler.antenna_arr.rotation
normalized_antenna_distance = cfg.data_handler.antenna_arr.normalized_antenna_distance

blensor_scenario_path = cfg.blensor_options.path_to_scenario
blensor_runfile_path = cfg.blensor_options.blensor_img_path

insite_study_area_name = cfg.base_files_names.insite_study_area_name
insite_tx_name = cfg.base_files_names.insite_tx_name
insite_rx_name = cfg.base_files_names.insite_rx_name
insite_setup_name = cfg.base_files_names.insite_setup_name
insite_vehicles_name = cfg.base_files_names.insite_vehicles_name

if use_vehicles_template:
    latitude, longitude = get_lat_long(base_insite_project_path)
    insite_vehicles_name_model = insite_vehicles_name
    insite_vehicles_name = insite_vehicles_name + '_'

if isolated_sim:
    results_base_model_dir = isolated_results_dir
else:
    results_base_model_dir = os.path.join(results_dir, 'base')

results_base_model_dir.replace('\\', '/')
setup_path = os.path.join(base_insite_project_path, insite_setup_name + '.setup')
base_setup_path = os.path.join(base_insite_project_path, 'base.setup')
base_x3d_xml_path = os.path.join(
    base_insite_project_path,
    'base.' + insite_study_area_name + '.xml')
paths_file_name = insite_setup_name + '.paths.t001_01.r002.p2m'
base_object_file_name = os.path.join(base_insite_project_path, "base.object")
base_txrx_file_name = os.path.join(base_insite_project_path, "base.txrx")
simulation_info_file_name = 'wri-simulation.info'

# Object which will be modified in the RWI project
dst_object_file_name = insite_vehicles_name + '.object'

# txrx which will be modified in the RWI project
dst_txrx_file_name = insite_setup_name + '.txrx'

# XML project that will be executed by InSite command line tools
# Its path will be the run folder.
dst_x3d_xml_file_name = (
    insite_setup_name
    + '.'
    + insite_study_area_name
    + '.xml'
)

# print('Output JSON file: ', simulation_info_file_name)
# print('Reference InSite model: ', base_x3d_xml_path)
# print('Generated InSite model that will be used: ', dst_x3d_xml_file_name)
# print('Reference .object file: ', base_object_file_name)
# print('Generated .object file that will be used: ', dst_object_file_name)
# print('Reference .txrx file: ', base_txrx_file_name)
# print('Generated .txrx file that will be used: ', dst_txrx_file_name)


# The mysterious information below is added in simulation.py into an XML file
if insite_version == '3.3':
    dst_x3d_txrx_xpath = (
        "./remcom__rxapi__Job/Scene/remcom__rxapi__Scene/TxRxSetList/"
        "remcom__rxapi__TxRxSetList/TxRxSet/remcom__rxapi__PointSet/"
        "OutputID/remcom__rxapi__Integer[@Value='2']"
        + "/../../ControlPoints/remcom__rxapi__ProjectedPointList"
    )

    dst_x3d_txrx_xpath_to_tx = (
        "./remcom__rxapi__Job/Scene/remcom__rxapi__Scene/TxRxSetList/"
        "remcom__rxapi__TxRxSetList/TxRxSet/remcom__rxapi__PointSet/"
        "OutputID/remcom__rxapi__Integer[@Value='1']"
        + "/../../ControlPoints/remcom__rxapi__ProjectedPointList"
    )

else:
    dst_x3d_txrx_xpath = (
        "./Job/Scene/Scene/TxRxSetList/TxRxSetList/TxRxSet/"
        "PointSet/OutputID/Integer[@Value='2']"
        + "/../../ControlPoints/ProjectedPointList"
    )

    dst_x3d_txrx_xpath_to_tx = (
        "./Job/Scene/Scene/TxRxSetList/TxRxSetList/TxRxSet/"
        "PointSet/OutputID/Integer[@Value='1']"
        + "/../../ControlPoints/ProjectedPointList"
    )


if isolated_sim:
    use_sumo = False
else:
    use_sumo = True


# Dimensions of the Mobile Objects, MOBJS, which will be placed on dst_object_file_name
# car_dimensions = (1.76, 4.54, 1.47)
car_dimensions = (2, 6, 1.47)

# Antenna to be placed above the cars
antenna_origin = (
    car_dimensions[0] / 2,
    car_dimensions[1] / 2,
    car_dimensions[2]
)

# ID of the car material.
# Must be defined on base_object_file_name and it is processed by simulation.py.
car_material_id = 0
car_structure_name = 'car'

# Name of the antenna points in base_txrx_file_name
antenna_points_name = insite_rx_name


if use_sumo is True:
    seed = cfg.seed
    np.random.seed(seed)

    sumo_cmd = [
        sumo_bin,
        '-c',
        sumo_cfg,
        '--step-length',
        str(sampling_interval),
        '--seed',
        '{}'.format(seed)
    ]

    # Mapping from SUMO to InSite coordinates.
    # Take only min and max for x and y and put there.
    lane_boundary_dict = {
        "laneA_0": [[758.5, 460], [744.5, 660]],
        "laneB_0": [[658.82, 460], [747.5, 358.76]],
        "laneC_0": [[658.82, 460], [752.5, 675.90]],
        "laneD_0": [[840.08, 460], [755.5, 660]]
    }

else:
    # Not sure if this is ancient code used for debugging with use_sumo = False.

    # Origin and destination of the line to place the cars
    line_origin = (
        (755.25, 470, 0.2),
        (755.25 + 5, 470, 0.2),
    )

    # Dimension line_destination is indicating to
    line_destination = 645
    line_dimension = 1

    # Distance between cars
    def car_distances():
        return np.random.uniform(1.5, 6)

