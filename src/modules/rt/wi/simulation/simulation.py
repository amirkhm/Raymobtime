import os
import shutil
import numpy as np
import logging
import json
import traci
from src.scripts.helpers import format_run_name
from src.modules.mobility.sumo.check_sumo import check_sumo_simulation_status
from src.modules.rt.wi import check_wi_run_status
from src.modules.rt.wi.modeling import  X3dXmlFile3_3
from src.modules.rt.wi.simulation.tools import *
from src.modules.rt.wi.modeling import (
    insite, 
    X3dXmlFile, 
    objects, 
    txrx)
from src.modules.rt.wi.simulation.placement import (
    place_on_line, 
    place_by_sumo)

def onlyDronesList(idList):
    """
    Filter a SUMO vehicle ID list to keep only drone vehicles.

    This function removes all vehicle IDs that do not start with ``"dflow"``.
    It is used when the simulation should consider only drone mobility flows.

    Args:
        idList: List of SUMO vehicle identifiers.

    Returns:
        The filtered list containing only drone vehicle identifiers.
    """
    for v_id, veh in enumerate(idList[:]):
        if not veh.startswith('dflow'):
            idList.remove(veh)
    return idList

def wireless_insite_simulation(c):
    """
    Run Wireless InSite ray-tracing simulations for the configured runs.

    This function validates configuration constraints, creates a Wireless InSite
    project runner, and executes the ray-tracing simulation through the
    configured batch executable. It supports both isolated simulations and
    regular Raymobtime simulations over multiple run folders.

    In isolated mode, the function runs a single Wireless InSite project from
    the isolated results directory. In regular mode, it iterates over the
    configured run indices and executes Wireless InSite for each run that does
    not already contain the expected path output file, unless cleaning or jump
    behavior is enabled.

    Args:
        c: Runtime configuration object containing Wireless InSite paths,
            execution flags, output directories, run indices, study area name,
            setup name, and batch executable path.

    Returns:
        None.

    Raises:
        Exception: If incompatible configuration flags are enabled, if a required
            output file already exists and cannot be overwritten, or if fixed
            receiver configuration is inconsistent.
        subprocess.CalledProcessError: If the Wireless InSite batch execution
            fails.
    """
    if c.fixed_receivers and c.receivers_per_episode != 0:
        # At fixed receivers, position set on WI is maintained, 
        # that manner it should not change here, default zero.
        logging.error(f'if flag fixed_receivers=True, receivers_per_episode must be 0 but it is {c.receivers_per_episode}')
        raise Exception()
    if c.isolated_sim and c.vehicles_template:
        # isolated sim is intended to be static, no object is placed after modelling.
        logging.error('flags isolated_sim=True and vehicles_template=True are not compatible')
        raise Exception()

    insite_project = insite.InSiteProject(
        project_name='model',
        wibatch_bin=c.wibatch_bin)

    logging.info(
        '\033[92m'
        'Ray traing simulation started'
        '\033[0m')

    logging.debug('Ray-tracing will start.')

    if c.isolated_sim:
        run_dir = os.path.join(c.isolated_results_dir)
        #Ray-tracing output folder (where InSite will store the results (Study Area name)).
        #They will be later copied to the corresponding output folder specified by results_dir
        project_output_dir = os.path.join(run_dir, c.insite_study_area_name) #output InSite folder

        p2mpaths_file = os.path.join(project_output_dir, c.insite_setup_name + '.paths.t001_01.r002.p2m')
        if not os.path.exists(p2mpaths_file) or ('rt' in c.base_config.clean_previous):
            xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
            xml_full_path=xml_full_path.replace(' ', '\ ')
            insite_project.run_x3d(xml_full_path, project_output_dir)
        else: 
            raise Exception(f'{p2mpaths_file} already exists')
        return
    else:
        for i in c.n_run:
            run_dir = os.path.join(c.results_dir, format_run_name(i))
            #Ray-tracing output folder (where InSite will store the results (Study Area name)).
            #They will be later copied to the corresponding output folder specified by results_dir
            project_output_dir = os.path.join(run_dir, c.insite_study_area_name) #output InSite folder

            p2mpaths_file = os.path.join(project_output_dir, c.insite_setup_name + '.paths.t001_01.r002.p2m')
            if not os.path.exists(p2mpaths_file) or ('rt' in c.base_config.clean_previous):
                xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
                xml_full_path=xml_full_path.replace(' ', '\ ')
                insite_project.run_x3d(xml_full_path, project_output_dir)
            elif os.path.exists(p2mpaths_file) and c.jump:
                continue
            else: 
                raise Exception(f'{p2mpaths_file} already exists')
            
    logging.info(
        '\033[92m'
        'Finished running ray-tracing'
        '\033[0m')

def copytree_base_files(c):
    """
    Copy the base Wireless InSite project files to the output model directory.

    This function copies the base Wireless InSite project folder into the
    Raymobtime output folder. If the destination already exists and
    ``clean_previous`` is enabled, the old results directory is removed and the
    base project is copied again. If the destination exists and mobility is
    enabled without cleaning, an error is raised to avoid overwriting previous
    results.

    Args:
        c: Runtime configuration object containing the base project path,
            output model directory, result directory, mobility flags, and
            cleaning options.

    Returns:
        None.

    Raises:
        FileExistsError: If the destination folder already exists and the
            configuration does not allow overwriting it.
        FileNotFoundError: If the base Wireless InSite project folder does not
            exist.
        OSError: If copying or removing folders fails.
    """
    #copy files from initial (source folder) to results base folder
    try:
        shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
    except FileExistsError:
        logging.error(
            '\033[91m'
            f'Folder/file already exists:\n'
            '\033[90m'
            f'{c.results_base_model_dir}. \n'
            '\033[0m')
        raise FileExistsError
    logging.info(
        '\033[92m'
        f'Copying scnario to output folder. \n'
        '\033[90m'
        f'   Copied folder {c.base_insite_project_path} \n'
        f'   into {c.results_base_model_dir}'
        '\033[0m')

def mobility_sumo(c):
    """
    Generate Wireless InSite simulation scenes from SUMO mobility data.

    This function reads the base Wireless InSite object and transmitter/receiver
    files, starts a SUMO simulation through TraCI, selects receiver and
    transmitter vehicles according to the configuration, places vehicles,
    pedestrians, and antennas into each scene, and writes the modified Wireless
    InSite files for each generated run.

    The function supports SUMO-based mobility, optional V2V simulations, drone
    filtering, area-limited receiver selection, fixed receivers, pedestrian
    placement, detailed vehicle templates, and XML updates for transmitter and
    receiver positions. It also writes per-run metadata and SUMO output
    information files.

    Args:
        c: Runtime configuration object containing SUMO command settings,
            mobility options, Wireless InSite base files, output paths,
            antenna names, receiver/transmitter counts, scene and episode
            settings, V2V options, pedestrian options, and template settings.

    Returns:
        None. The generated simulation folders and modified Wireless InSite files
        are written to disk.

    Raises:
        FileNotFoundError: If required base object, TX/RX, XML, or project files
            are missing.
        FileExistsError: If a run directory cannot be created or copied.
        KeyError: If expected transmitter/receiver names are missing from the
            parsed TX/RX file.
        RuntimeError: If SUMO/TraCI fails during simulation execution.
    """
    #* Open files for parsing ============================================================
    #open InSite files that are used as the base to create each new scene / simulation
    with open(c.base_object_file_name) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    logging.debug(
        '\033[36m'
        f'Objects\n'
        '\033[90m'
        f'   Opened file with objects: {c.base_object_file_name}'
        '\033[0m')
    with open(c.base_txrx_file_name) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    logging.debug(
        '\033[36m'
        f'Transmitters and Receivers file\n'
        '\033[90m'
        f'   Opened file with transmitters and receivers: {c.base_txrx_file_name}'
        '\033[0m')

    #* End Open files for parsing ============================================================

    antenna = txrxFile[c.insite_rx_name].location_list[0]

    if c.mobility.enabled and c.mobility.tool == 'line':
        # creates a car structure to be placed on the line
        car = objects.RectangularPrism(*c.car_dimensions, material=c.car_material_id)
        car_structure = objects.Structure(name=c.car_structure_name)
        car_structure.add_sub_structures(car)
        car_structure.dimensions = car.dimensions

        n_runs_wiout_rx = 0 # Number of Runs without
        for i in c.n_run:
            run_dir = os.path.join(
                c.results_dir, 
                format_run_name(i - n_scenes_without_channels))
            objFile.clear()
            structure_group, location = place_on_line(
                c.line_origin, 
                c.line_destination, 
                c.line_dimension,
                c.car_distances, 
                car_structure, 
                antenna, 
                c.antenna_origin)
            

    elif c.mobility.enabled and c.mobility.tool == 'sumo':
        np.random.seed(c.sumo.seed)
        logging.info(
            '\033[92m'
            'Mobility:SUMO (Starting placement)'
            '\033[0m')
        traci.start(c.sumo_cmd)

        scene_i = 0
        episode_i = -1

        #======================================================================================
        # Jumps to the defined traci start
        #======================================================================================
        for tmp_var in range(int(c.n_run[0])):
            # Only when switching episodes or for the first time choose vehicles to be receivers
            if scene_i == 0:
                while True:
                    # ensures number of receivers at beginning of episode
                    traci_vehicle_IDList = traci.vehicle.getIDList()
                    # Only drone, remove the non-drone vehicles from the list
                    if c.drone_simulation:
                        traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                    if len(traci_vehicle_IDList) < c.receivers_per_episode:
                        traci.simulationStep()
                        logging.warning(
                            '\033[35m'
                            f'At run {tmp_var}: not enough vehicles at time {traci.simulation.getTime()}'
                            '\033[0m')
                    else:
                        break
                veh_with_antenna = np.random.choice(
                    traci_vehicle_IDList, 
                    c.receivers_per_episode, 
                    replace=False)
            else:
                # step at time scene or episode
                scene_i += 1
                if scene_i <= c.scenes_per_episode:
                    traci.simulationStep()
                else:
                    scene_i = 0
                    episode_i += 1
                    for _ in range(c.time_between_episodes):
                        traci.simulationStep()
            logging.info(
                '\033[97m'
                f'Jump until the step {c.n_run[0]}: {int((tmp_var/c.n_run[0])* 100)}%'
                '\033[0m')
    
        #======================================================================================
        # start the loop to create the scenes and episodes
        #======================================================================================
        n_scenes_without_channels = 0 # Without Tx or Rx
        for i in c.n_run:
            run_dir = os.path.join(
                c.results_dir,
                format_run_name(i - n_scenes_without_channels))
            objFile.clear()

            if scene_i >= c.scenes_per_episode or (episode_i == -1):
                # Step episode and reset scene
                episode_i += 1
                scene_i = 0
                # step time_between_episodes
                if episode_i > 0:
                    for _ in range(c.time_between_episodes):
                        traci.simulationStep()
                #======================================================================================
                # choose vehicles to be receivers or transmitters at the beginning of episode
                #======================================================================================
                if c.fixed_receivers:
                    #======================================================================================
                    # no vehicles with antennas, only fixed transmitter and receivers.
                    #======================================================================================
                    veh_with_antenna = []
                    Tx_veh = None
                    antenna_Tx = None
                else:
                    #======================================================================================
                    # Choose vehicles to carry receivers and transmitters, if applicable, at the beginning of episode
                    #======================================================================================
                    # ensure that there enough cars to place antennas. 
                    # If fixed_receivers, then wait to have at least
                    # one vehicle
                    if c.V2V: # ensure that there enough vehicles to Rx and Tx antennas
                        min_vehicles = (c.receivers_per_episode + c.n_Tx_per_episode)
                    else:
                        min_vehicles = c.receivers_per_episode

                    enough_vehicles = True
                    while 1:
                        # Take vehicles of interest, if specified
                        if c.drone_simulation: 
                            traci_vehicle_IDList = onlyDronesList(
                                traci.vehicle.getIDList())
                        else:
                            traci_vehicle_IDList = traci.vehicle.getIDList()

                        # Take vehicles only from the specified area, if specified
                        if c.set_area_limit:
                            veh, n_veh = pick_veh_from_area(
                                traci_vehicle_IDList, 
                                [c.min_lim, c.max_lim], 
                                min_vehicles, 
                                return_counts=True)
                        else:
                            n_veh = len(traci_vehicle_IDList)
                            veh = traci_vehicle_IDList
                        
                        if n_veh < min_vehicles:
                            if enough_vehicles == True:
                                enough_vehicles = False
                                logging.warning(
                                    '\033[35m'
                                    f'{format_run_name(i - n_scenes_without_channels)}:'
                                    f'Not enough vehicles in the area at time {traci.simulation.getTime()}'
                                    '\033[0m')
                            traci.simulationStep()
                        else:
                            if enough_vehicles == False:
                                logging.warning(
                                    '\033[35m'
                                    f'{format_run_name(i - n_scenes_without_channels)}:'
                                    f'Enough vehicles in the area at time {traci.simulation.getTime()}'
                                    '\033[0m')
                            break

                    # Choose vehicles
                    veh_with_antenna = np.random.choice(
                        veh, 
                        min_vehicles, 
                        replace=False)

                    # Chose which vehicles selected are Tx and which are Rx
                    if c.V2V:
                        # chooses the Tx veh
                        Tx_veh = np.random.choice(
                            traci_vehicle_IDList, 
                            c.n_Tx_per_episode, 
                            replace=False)
                        traci_vehicle_IDList = [x for x in traci_vehicle_IDList if x not in Tx_veh]
                        # chooses a minor number of Rx vehicles closest to Tx to remain receivers
                        if c.close_vehicles: # Only works for 1 Tx
                            x, y = traci.vehicle.getPosition(Tx_veh[0])
                            pos_Tx = np.array(traci.simulation.convertGeo(x, y))
                            Rx_name = {}
                            all_distances = []
                            for veh in traci_vehicle_IDList:
                                x, y = traci.vehicle.getPosition(veh)
                                pos_Rx = np.array(traci.simulation.convertGeo(x, y))
                                dist = (np.sqrt(np.sum((pos_Tx-pos_Rx)**2)))
                                Rx_name[dist] = veh
                                all_distances.append(dist)
                            all_distances = np.sort(all_distances)[:c.n_of_vehicles]
                            traci_vehicle_IDList = [Rx_name[i] for i in all_distances]
                            c.receivers_per_episode = c.n_of_vehicles

                        veh_with_antenna = np.random.choice(
                            traci_vehicle_IDList, 
                            c.receivers_per_episode, 
                            replace=False)

                        antenna_Tx = txrxFile[c.insite_tx_name].location_list[0]
                    else:
                        Tx_veh = None
                        antenna_Tx = None
            else:
                traci.simulationStep()

            structure_group, location, location_Tx, str_vehicles = place_by_sumo(
                c,
                antenna,
                antenna_Tx,
                c.car_material_id,
                lane_boundary_dict=c.lane_boundary_dict,
                veh_with_antenna=veh_with_antenna,
                Tx_veh=Tx_veh,
                V2V=c.V2V,
                fixed_receivers = c.fixed_receivers,
                use_pedestrians = c.use_pedestrians)
            
            # if no vehicles in scene, save the information and jump to the next scene
            if traci.vehicle.getIDList() is None:
                # no vehicles in the environment (no vehicles at all)
                logging.info("No vehicles in scene " + str(scene_i) + " time " + str(traci.simulation.getCurrentTime()))
                os.makedirs(run_dir + '_novehicles') #create an empty folder to "indicate" the situation
                #save SUMO information for this scene as text CSV file
                sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName_novehicles.txt')
                writeSUMOInfoIntoFile(
                    c, 
                    sumoOutputInfoFileName, 
                    episode_i, 
                    scene_i, 
                    c.lane_boundary_dict, 
                    veh_with_antenna)
                scene_i += 1 #update scene counter
                continue

            # if no vehicles with antennas in scene, save the information and jump to the next episode
            if (location is None) or (c.V2V and location_Tx is None):
                if not c.fixed_receivers:
                    n_scenes_without_channels = n_scenes_without_channels + 1
                    # Not reason to continue (no receivers anymore), go to next episode
                    logging.warning("No vehicles with antennas in scene " + str(scene_i) + " time " + str(traci.simulation.getCurrentTime()))
                    os.makedirs(run_dir + '_noAntennaVehicles') #create an empty folder to "indicate" the situation
                    scene_i = np.Infinity
                    continue

            # Parsing =====================================================================================
            # Toda run limpa o objfile
            objFile.clear()

            # if use wireless insite copy base ============================================================
            shutil.copytree(c.base_insite_project_path, run_dir)
            logging.debug(
                '\033[92m'
                f'{format_run_name(i - n_scenes_without_channels)} \n'
                '\033[90m'
                f'   Copied {c.base_insite_project_path} \n'
                f'   into {run_dir}'
                '\033[0m')

            # writes at a run
            objFile.add_structure_groups(structure_group)
            dst_object_full_path = os.path.join(run_dir, c.dst_object_file_name)
            objFile.write(dst_object_full_path)

            #write new model of vehicles to the final folder
            if c.vehicles_template:
                dst_new_object_full_path = os.path.join(run_dir, c.insite_vehicles_name_model + '.object')
                f_dst_new_object = open(dst_new_object_full_path,'w')
                f_dst_new_object.write(str_vehicles)
                f_dst_new_object.close()

            if c.insite_version == '3.3':
                x3d_xml_file = X3dXmlFile3_3(c.base_x3d_xml_path)
            else:
                x3d_xml_file = X3dXmlFile(c.base_x3d_xml_path)
            logging.debug(
                '\033[36m'
                f'InSite XML\n'
                '\033[90m'
                f'   Opened file: {c.base_x3d_xml_path}'
                '\033[0m')
            #get name of XML
            xml_full_path = os.path.join(
                run_dir, 
                c.dst_x3d_xml_file_name) #input InSite folder
            xml_full_path=xml_full_path.replace(' ', '\ ')

            if not c.fixed_receivers:
                x3d_xml_file.add_vertice_list(
                    location, 
                    c.dst_x3d_txrx_xpath)
                if c.V2V:
                    x3d_xml_file.add_vertice_list(
                        location_Tx, 
                        c.dst_x3d_txrx_xpath_to_tx)
                x3d_xml_file.write(xml_full_path)

                # add vertices from receivers to the txrx file
                txrxFile[c.insite_rx_name].location_list[0] = location
                if c.V2V:
                    txrxFile[c.insite_tx_name].location_list[0] = location_Tx # add vertices from transmitters to the txrx file
                # txrx modified in the RWI project
                dst_txrx_full_path = os.path.join(run_dir, c.dst_txrx_file_name)
                txrxFile.write(dst_txrx_full_path)

            with open(os.path.join(run_dir, c.simulation_info_file_name), 'w') as infofile:
                if c.V2V:
                    info_dict = dict(
                        veh_with_antenna=list(veh_with_antenna),
                        Tx_veh=list(Tx_veh),
                        scene_i=scene_i)
                else:
                    info_dict = dict(
                        veh_with_antenna=list(veh_with_antenna),
                        scene_i=scene_i)
                json.dump(info_dict, infofile)

            #save SUMO information for this scene as text CSV file
            sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName.txt')
            writeSUMOInfoIntoFile(
                c,
                sumoOutputInfoFileName, 
                episode_i, scene_i, 
                c.lane_boundary_dict, 
                veh_with_antenna, 
                Tx_veh, 
                c.fixed_receivers, 
                c.use_pedestrians)

            scene_i += 1 #update scene counter
        
        traci.close()
        logging.info(
            '\033[92m'
            'Finished SUMO placement'
            '\033[0m')

def main(c):
    """
    Run the Raymobtime Wireless InSite simulation pipeline.

    This function is the entry point for the Wireless InSite simulation module.
    It first copies the base project files to the output directory, then runs
    SUMO-based mobility generation if enabled, and finally executes the
    Wireless InSite ray-tracing simulation if requested in the configuration.

    Args:
        c: Runtime configuration object containing all mobility, ray-tracing,
            file path, and output settings required by the simulation pipeline.

    Returns:
        None.
    """
        
    if c.mobility.enabled and c.mobility.tool == 'sumo':
        if 'mobility' in c.clean_previous:
            # clean folder
            if os.path.exists(c.results_dir):
                shutil.rmtree(c.results_dir)
                logging.info(
                    '\033[92m'  # green
                    f'Cleanning output folder.\n'
                    '\033[90m'  # black
                    f'   Removed folder: {c.results_dir}'
                    '\033[0m')  # default collor
            # execute
            copytree_base_files(c)
            mobility_sumo(c)
            # check okay
            mobility_okay = check_sumo_simulation_status(c)
        else:
            # Check
            mobility_okay = check_sumo_simulation_status(c)
            if not (mobility_okay and c.resume):
                # execute
                copytree_base_files(c)
                mobility_sumo(c)
                # check okay
                mobility_okay = check_sumo_simulation_status(c)

    if c.ray_tracing.enabled:
        if 'rt' in c.clean_previous:
            # remove study folder of every run
            runs = c.rmt.sampling_parameters[1]
            for run in range(runs):
                folder = os.path.join(
                    c.results_dir, 
                    format_run_name(run), 
                    c.insite_study_area_name)
                if os.path.exists(folder):
                    shutil.rmtree(folder)
            # execute rt
            wireless_insite_simulation(c)
            rt_okay = check_wi_run_status(c)
        else:
            rt_okay = check_wi_run_status(c)
            print("i heve been here")
            if not (rt_okay and c.resume):
                wireless_insite_simulation(c)
                rt_okay = check_wi_run_status(c)