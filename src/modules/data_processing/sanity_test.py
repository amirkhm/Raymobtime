import os
import pandas as pd
import numpy as np
import h5py

def csv_check(main_folder):
    """
    Check the coordinate CSV file for valid and invalid channel entries.

    This function loads the ``CoordVehicleTxRx.csv`` file from the given
    simulation data folder, counts valid and invalid channel entries, reports
    episodes containing invalid entries, and prints a summary of the expected
    and observed number of channels.

    Args:
        main_folder: Path to the main simulation data folder containing the
            ``CoordVehicleTxRx.csv`` file.

    Returns:
        A tuple containing:
            - df_coord: Full coordinate dataframe.
            - df_val: Dataframe containing only valid channel entries.

    Raises:
        FileNotFoundError: If the coordinate CSV file does not exist.
        KeyError: If required columns such as ``Val``, ``EpisodeID``,
            ``SceneID``, ``RxID``, or ``TxID`` are missing.
    """
    csv_file = os.path.join(
        main_folder, 
        'CoordVehicleTxRx.csv')
    df_coord = pd.read_csv(csv_file)
    valid_channels = df_coord['Val'].value_counts()['V']
    if 'I' in df_coord['Val'].values:
        invalid_channels =  df_coord['Val'].value_counts()['I']
    else:
        invalid_channels = 0  # Return an empty DataFrame
    df_inv = df_coord[df_coord['Val'] == 'I']
    df_val = df_coord[df_coord['Val'] == 'V']
    #TODO retornar a contagem de únicos e achar episódios inteiros invalidos
    ep_inv = np.unique(df_inv['EpisodeID'])
    print("###### Coord File Check up ######")
    print(f'Invalid channels = {invalid_channels}')
    print(f'Valid channels = {valid_channels}')
    ep = max(df_coord['EpisodeID'])+1
    scene = max(df_coord['SceneID'])+1
    rx = max(df_coord['RxID'])+1
    tx = max(df_coord['TxID'])+1
    print(f'Total number of Channels = {valid_channels+invalid_channels} and should have {ep*scene*(rx+tx)}')
    print(f'Episodes with Invalid = {ep_inv}')
    print(f'dataframe with invalid channels = {df_inv}')
    print("###### Coord File Check up Finished ######")
    return df_coord, df_val

def ray_check(main_folder, df_val):
    """
    Check ray-tracing HDF5 files for invalid values in valid channels.

    This function verifies whether channels marked as valid in the coordinate
    dataframe contain NaN values in the corresponding ray-tracing HDF5 files.
    If a valid episode, scene, and receiver combination contains NaN values,
    an error message is printed.

    Args:
        main_folder: Path to the main simulation data folder containing the
            ``rays`` directory.
        df_val: Dataframe containing only valid channel entries from
            ``CoordVehicleTxRx.csv``.

    Returns:
        None. The function prints the validation results to the terminal.

    Raises:
        FileNotFoundError: If an expected ray HDF5 file does not exist.
        KeyError: If required dataframe columns are missing.
        OSError: If an HDF5 file cannot be opened.
    """
    print("###### Ray Files Check up ######")
    eps = np.unique(df_val['EpisodeID'].values)
    valid = list(zip(df_val['EpisodeID'], df_val['SceneID'], df_val['RxID']))
    for ep in eps:
        ray_file = os.path.join(main_folder, 'rays', f'rays_ep{ep}.hdf5')
        h5_data = h5py.File(ray_file)
        ray_data = np.array(h5_data.get('allEpisodeData'))
        scene, rx = np.where(np.isnan(ray_data)[:,:,0,0])
        for s, r in zip(scene,rx):
            if (ep,s,r) in valid:
                print(f'Error: Valid episode {ep} scene {s} and rx {r} with nan values in file {ray_file}')
    print("###### Ray Files Check up Finished ######")

def beam_check(main_folder, df_val):
    """
    Check beam-selection output files for invalid values in valid channels.

    This function loads the beam index and channel magnitude output files,
    checks for NaN values, and reports cases where valid episode, scene, and
    receiver combinations contain invalid beam or channel data. It also prints
    the total number of valid and invalid entries found in the beam outputs.

    Args:
        main_folder: Path to the main simulation data folder containing the
            ``beams`` directory.
        df_val: Dataframe containing only valid channel entries from
            ``CoordVehicleTxRx.csv``.

    Returns:
        None. The function prints the validation results to the terminal.

    Raises:
        FileNotFoundError: If the beam or channel output files do not exist.
        KeyError: If expected arrays are missing from the ``.npz`` files.
        ValueError: If the loaded arrays have unexpected shapes.
    """

    print("###### Beams Files Check up ######")
    valid = list(zip(df_val['EpisodeID'], df_val['SceneID'], df_val['RxID']))

    beam_file = os.path.join(main_folder, 'beams', 'beam_output.npz')
    beam_data = np.load(beam_file)['beam_index_array']

    episode, scene, rx = np.where(np.isnan(beam_data))
    for e, s, r in zip(episode, scene,rx):
        if (e,s,r) in valid:
            print(f'Error: Valid episode {e} scene {s} and rx {r} with nan values in file {beam_file}')
    print(f'Number of Valid Beams = {np.prod(beam_data.shape[:3])-len(episode)}')
    print(f'Number of Invalid Beams = {len(episode)}')

    beam_magnitude_file = os.path.join(main_folder, 'beams', 'channel_output.npz')
    beam_magnitude_data = np.load(beam_magnitude_file)['channel_array']

    episode, scene, rx = np.where(np.isnan(beam_magnitude_data)[:,:,:,0,0])
    for e, s, r in zip(episode, scene,rx):
        if (e,s,r) in valid:
            print(f'Error: Valid episode {e} scene {s} and rx {r} with nan values in file {beam_magnitude_file}')

    print(f'Number of Valid Channels = {np.prod(beam_magnitude_data.shape[:3])-len(episode)}')
    print(f'Number of Invalid Channels = {len(episode)}')

    print("###### Beams Files Check up Finished ######")

def sanity_check_up(c):
    """
    Run sanity checks over coordinate, ray, and beam output files.

    This function builds the main simulation data folder path from the runtime
    configuration, ensures the folder exists, and sequentially runs coordinate
    CSV checks, ray file checks, and beam output checks.

    Args:
        c: Runtime configuration object containing the working directory and
            output name used to locate the generated simulation data.

    Returns:
        None. The function prints check-up results to the terminal.

    Raises:
        FileNotFoundError: If required coordinate, ray, or beam output files are
            missing.
        KeyError: If required configuration fields or dataframe columns are
            missing.
    """
    
    main_folder = c.result_dir_processed_data
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)
    df, df_val = csv_check(main_folder)
    ray_check(main_folder, df_val)
    beam_check(main_folder, df_val)