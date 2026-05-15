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
    model_file = open(os.path.join(base_insite_project_path, 'model.study.xml'), 'r')
    insite_version = False

    for line in model_file:
        if '<InSite version="' in line:
            insite_version = line.split('version=')[1].split(' ')[0][1:4]
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


###############################################################
## Most information in this configuration file is used in the Stage 1 of
## the three stages below. But some are also used in the other stages.
## Stage 1: Running the ray-tracing (RT) and traffic simulators
## Stage 2: Organizing raw data into a 5GMdata database
## Stage 3: Converting the database into a file suitable to machine learning packages such as Keras
## This file is split into two parts. In most cases Part II is not modified.
###############################################################

# Read typical information from config.yaml
cfg = load_config()

###############################################################
## Part I - Basic information that typically needs to be modified / checked
###############################################################

# Current folder (or directory). Some paths are relative to this folder:
working_directory = os.path.dirname(os.path.realpath(__file__))

# InSite will look for input files in this folder. These files will be used to generate all simulations
base_insite_project_path = os.path.join(
    working_directory,
    'base_files',
    cfg.simulation_paths.base_insite_path
)

# Folder to store each InSite project and its results
# Will create subfolders for each "run", run0000, run0001, etc.
results_dir = os.path.join(
    working_directory,
    'simulations',
    cfg.simulation_paths.results_dir_path
)

isolated_results_dir = os.path.join(
    results_dir,
    cfg.simulation_paths.base_insite_path
)

# Folders and files for InSite and its license.
# For Windows you may simply inform the path to the executable files,
# not minding about the license file location.
# Folders for SUMO and InSite.
# Use executable sumo-gui if want to see the GUI or sumo otherwise.

sim_name = cfg.simulation_paths.results_dir_path
isolated_sim = cfg.features.isolated_simulation

# Identify InSite version
insite_version = get_insite_version(base_insite_project_path)

# InSite env variable
locale = 'LC_CTYPE=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8 LC_TIME=en_US.UTF-8 '

if insite_version == '3.3':
    wibatch_bin = (
        locale
        + '{} '.format(cfg.insite_paths.REMCOMINC_LICENSE_FILE)
        + 'LD_LIBRARY_PATH={}/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ '.format(
            cfg.insite_paths.insite_software_path
        )
        + '{}/WirelessInSite/3.3.0.4/Linux-x86_64RHEL6/bin/wibatch'.format(
            cfg.insite_paths.insite_software_path
        )
    )

elif insite_version == '3.2':
    wibatch_bin = (
        locale
        + '{} '.format(cfg.insite_paths.REMCOMINC_LICENSE_FILE)
        + 'LD_LIBRARY_PATH=/{}/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ '.format(
            cfg.insite_paths.insite_software_path
        )
        + '{}/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/wibatch'.format(
            cfg.insite_paths.insite_software_path
        )
    )

n_run = range(1)

# Set to False if only vehicles are receivers
use_fixed_receivers = cfg.features.use_fixed_receivers

# Only set True if your SUMO is ready for pedestrians
use_pedestrians = cfg.features.use_pedestrians

# Set True to use pre-made vehicle, not boxes.
# NOTE: only set True if you have the folder objects with the models.
use_vehicles_template = cfg.features.use_vehicles_template

# Only drones will be chosen to be receivers
drone_simulation = cfg.features.drone_simulation

# Only available for a single Rx
mimo_orientation = cfg.features.mimo_orientation

# Set True to use V2V, where transmitters and receivers are vehicles
use_V2V = cfg.features.use_V2V


if not isolated_sim:
    ### HERE STARTS CONFIGURATION ###
    ### NOTE: ONLY CHANGE IF YOU KNOW WHAT YOU ARE DOING

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

    # print('########## Scripts will assume the following files: ##########')
    # print('SUMO executable: ', sumo_bin)
    # print('SUMO configuration: ', sumo_cfg)
    # print('InSite calcprop executable: ', calcprop_bin)
    # print('InSite wibatch executable: ', wibatch_bin)
    # print('Working folder (base for several folders): ', working_directory)
    # print('InSite input files folder: ', base_insite_project_path)
    # print('Final output parent folder: ', results_dir)

    # Iterator that determines maximum number of RT simulations
    n_run = range(
        cfg.simulation_parameters.n_init_run,
        cfg.simulation_parameters.n_end_run,
        1
    )

    # Time interval between scenes, in seconds
    sampling_interval = float(cfg.simulation_parameters.sampling_interval)

    # Number of scenes of each episode
    time_of_episode = int(cfg.simulation_parameters.n_scenes_of_each_episode)

    # Time among episodes, in steps
    # If you specify x/Ts, then x is in seconds
    time_between_episodes = int(
        float(cfg.simulation_parameters.time_between_episodes) / sampling_interval
    )


if use_fixed_receivers:
    # Number of receivers per episode
    n_antenna_per_episode = 0
else:
    # Number of receivers per episode
    n_antenna_per_episode = cfg.simulation_parameters.n_antenna_per_episode


if use_V2V:
    # Number of transmitters per episode
    n_Tx_per_episode = cfg.simulation_parameters.n_Tx_per_episode

    # Number of receivers per episode
    n_antenna_per_episode = cfg.simulation_parameters.n_antenna_per_episode


# Where to map the receiver to TFRecords: minx, miny, maxx, maxy
analysis_area_enabled = cfg.data_handler.area_of_analyses.enabled
analysis_area = cfg.data_handler.area_of_analyses.coordinates_limits
analysis_area_resolution = 0.5

antenna_number = 10

# Frequency in Hz for the RT simulation
frequency = 60e9

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


###############################################################
## Part II - Extra information that typically does not need to be modified
## unless you changed the InSite model, using the GUI, for example.
###############################################################

# Fullfill this parameters with InSite's information
insite_study_area_name = cfg.base_files_names.insite_study_area_name
insite_tx_name = cfg.base_files_names.insite_tx_name
insite_rx_name = cfg.base_files_names.insite_rx_name
insite_setup_name = cfg.base_files_names.insite_setup_name
insite_vehicles_name = cfg.base_files_names.insite_vehicles_name


if use_vehicles_template:
    latitude, longitude = get_lat_long(base_insite_project_path)
    insite_vehicles_name_model = insite_vehicles_name
    insite_vehicles_name = insite_vehicles_name + '_'


##### Folders and files for InSite ####

# Copy of the RWI project used in the simulation
# AK-TODO: instead of "base", it should match the name InSite gives,
# to facilitate porting.
if isolated_sim:
    results_base_model_dir = isolated_results_dir
else:
    results_base_model_dir = os.path.join(results_dir, 'base')

results_base_model_dir.replace('\\', '/')

# Input files, which are read by the Python scripts

# File that has the base InSite project
setup_path = os.path.join(base_insite_project_path, insite_setup_name + '.setup')
base_setup_path = os.path.join(base_insite_project_path, 'base.setup')

# setup_path = setup_path.replace(' ', '\ ') # deal with paths with blank spaces

# XML that has information about the simulations
base_x3d_xml_path = os.path.join(
    base_insite_project_path,
    'base.' + insite_study_area_name + '.xml'
)

# Name, basename, of the paths file generated in the simulation
paths_file_name = insite_setup_name + '.paths.t001_01.r002.p2m'

# Base object file to generate the object_dst_file_name
base_object_file_name = os.path.join(base_insite_project_path, "base.object")

# Base txrx file to generate the txrx_dst_file_name
base_txrx_file_name = os.path.join(base_insite_project_path, "base.txrx")


# Output files, which are written by the Python scripts.
# Provide here only the names.
# The full paths will be created by simulation.py, using the run folder.

# Name, basename, of the JSON output simulation info file
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

