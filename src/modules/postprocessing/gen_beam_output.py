import numpy as np
import h5py
import os
from src.scripts.helpers import format_run_name
from src.modules.postprocessing.mimo_channels import (
    getNarrowBandUPAMIMOChannel, 
    getCodebookOperatedChannel,
    dft_codebook_upa, 
    rotate_vectors, 
    import_mimo_channel)

def count_hmatrix(dir):
    """
    Count Wireless InSite H-matrix files in a directory tree.

    This function recursively walks through the given directory and counts all
    files whose names start with ``hmatrix``. It is used to estimate the number
    of receivers when channel matrices are imported directly from Wireless
    InSite output files.

    Args:
        dir: Root directory where H-matrix files should be searched.

    Returns:
        Number of files whose names start with ``hmatrix``.
    """

    c = 0
    for _, _, file in os.walk(dir):
        for file in file:
            if file.startswith("hmatrix"):
                c += 1
    return c

def process_ep(path, c):
    """
    Process one episode and compute beam-selection outputs.

    This function generates MIMO channel matrices, applies transmit and receive
    codebooks, and computes the best beam index for each scene and receiver.
    The channel data can be obtained either from imported Wireless InSite
    H-matrix CSV files or from ray data stored in an HDF5 episode file.

    When H-matrix import is enabled, the function reads one H-matrix file per
    scene and receiver. Otherwise, it reads ray-tracing data from the provided
    HDF5 file and computes the narrowband UPA MIMO channel from path gains,
    phases, angles of departure, and angles of arrival.

    Args:
        path: Path to the HDF5 ray data file for the episode. This value can be
            ``None`` when H-matrix import is enabled.
        c: Runtime configuration object containing MIMO options, antenna array
            expansion, codebook paths, array rotation, normalized antenna
            spacing, simulation paths, and execution flags.

    Returns:
        A tuple containing:
            - hmatrix: MIMO channel matrices for each scene and receiver.
            - beamIndexOutputs: Best beam index for each scene and receiver.
            - channelOutputs: Magnitude of the codebook-operated equivalent
              channel for each scene and receiver.

    Raises:
        FileNotFoundError: If an expected H-matrix folder is not found.
        OSError: If the HDF5 file cannot be opened.
        ValueError: If ray data or imported channel data has an unexpected
            format.
    """

    import_precoding = c.import_precoding
    import_hmatrix = c.import_hmatrix
    import_combining = c.import_combining
    expansion = c.expansion
    rotation = c.rotation

    normalizedAntDistance = c.normalized_antenna_distance #0.5
    numOfInvalidChannels = 0
    
    if c.isolated_sim:
        numScenes = 1

    if  c.import_hmatrix:
        hmatrix_folder =  os.path.join(
            c.results_dir,
            c.insite_study_area_name,
            'HMatrixCategory')
        numReceivers = count_hmatrix(hmatrix_folder)
    else:
        h5_data = h5py.File(path)
        ray_data = np.array(h5_data.get('allEpisodeData'))
        numScenes = ray_data.shape[0]
        numReceivers = ray_data.shape[1]
    
    # if false use dft codebook else use path given to .npy
    # eg import_precoding = '~/phi_50.npy'
    if import_precoding == False:
        precoding = dft_codebook_upa(
            expansion['Tx'][0], # x
            expansion['Tx'][1]) # y
    else:
        precoding = np.load(import_precoding)
    
    # if false use dft codebook else use path given to .npy
    if import_combining == False:
        combining = dft_codebook_upa(
            expansion['Rx'][0], # x
            expansion['Rx'][1]) # y
    else:
        combining = np.load(import_combining)
        
    hmatrix = np.nan * np.ones(
        (numScenes, numReceivers), 
        np.matrix)
    channelOutputs = np.nan * np.ones((
        numScenes, 
        numReceivers, 
        combining.shape[1],
        precoding.shape[1]), 
        float)
    beamIndexOutputs = np.nan * np.ones(
        (numScenes, numReceivers), 
        np.int8)
        
    # if import channel, hmatrix.csv from WI. Mean that's a channel from 1 Tx to 1 Rx
    # eg import_hmatrix = 'hmatrix.txSet001.txPt001.rxSet002.inst001.csv'
    if import_hmatrix:
        for s in range(numScenes):
            if c.isolated_sim:
                hmatrix_folder =  os.path.join(
                    c.results_dir,
                    c.insite_study_area_name,
                    'HMatrixCategory')
            else:
                run = format_run_name(s)
                hmatrix_folder =  os.path.join(
                    c.results_dir,run,
                    c.insite_study_area_name,
                    'HMatrixCategory')

            if not os.path.exists(hmatrix_folder):
                raise FileNotFoundError(f'Not Found dir: {hmatrix_folder}')
               
            for r in range(numReceivers):
                hmatrix_file = os.path.join(
                    hmatrix_folder, 
                    f'hmatrix.txSet001.txPt001.rxSet00{r+2}.inst001.csv')
                if not os.path.isfile(hmatrix_file):
                    print(f'File {hmatrix_file} not found')
                    continue
                try:
                    mimoChannel = import_mimo_channel(hmatrix_file)
                    equivalentChannel = getCodebookOperatedChannel(mimoChannel, precoding, combining)
                    
                    hmatrix[s,r] = mimoChannel
                    equivalentChannelMagnitude = np.abs(equivalentChannel)
                    beamIndexOutputs[s,r] = int(np.argmax(equivalentChannelMagnitude, axis=None))
                    channelOutputs[s,r]=np.abs(equivalentChannel)

                except Exception as e:
                    print(f"An error occurred while processing receiver {r}: {e}")
                    continue
    else: # Calculate from rays data of HDF5
        for s in range(numScenes):  # 10
            for r in range(numReceivers):  # 2
                insiteData = ray_data[s, r, :, :]
                numNaNsInThisChannel = sum(np.isnan(insiteData.flatten()))
                if numNaNsInThisChannel == np.prod(insiteData.shape):
                    numOfInvalidChannels += 1
                    continue  # next Tx / Rx pair
                if numNaNsInThisChannel > 0:
                    numMaxRays = insiteData.shape[0]
                    for itemp in range(numMaxRays):
                        if sum(np.isnan(insiteData[itemp].flatten())) > 0:
                            insiteData = insiteData[:itemp-1,:] #replace by smaller array without NaN
                            break
                gain_in_dB = insiteData[:, 0]
                timeOfArrival = insiteData[:, 1]
                AoD_el = insiteData[:, 2]
                AoD_az = insiteData[:, 3]
                AoA_el = insiteData[:, 4]
                AoA_az = insiteData[:, 5]
                isLOSperRay = insiteData[:, 6]
                pathPhases = insiteData[:, 7] #or None
                
                # Negative used to define standard rotation positive counterclockwise on UPA
                AoD_az, AoD_el = rotate_vectors(AoD_az, AoD_el, -rotation['Tx'][0], -rotation['Tx'][1], -rotation['Tx'][2])
                AoA_az, AoA_el = rotate_vectors(AoA_az, AoA_el, -rotation['Rx'][0], -rotation['Rx'][1], -rotation['Rx'][2])
                
                mimoChannel = getNarrowBandUPAMIMOChannel(
                    AoD_el,AoD_az,AoA_el,AoA_az,
                    gain_in_dB,pathPhases,
                    expansion['Tx'][0], expansion['Tx'][1],
                    expansion['Rx'][0], expansion['Rx'][1],
                    normalizedAntDistance)
                equivalentChannel = getCodebookOperatedChannel(
                    mimoChannel, 
                    precoding, 
                    combining)

                equivalentChannelMagnitude = np.abs(equivalentChannel)
                hmatrix[s,r] = mimoChannel
                beamIndexOutputs[s,r] = int(np.argmax(equivalentChannelMagnitude, axis=None))
                channelOutputs[s,r]=np.abs(equivalentChannel)

    return hmatrix, beamIndexOutputs, channelOutputs

def gen_beam_output_file(c):
    """
    Generate and save beam-selection output files.

    This function processes the configured simulation data to compute MIMO
    channel matrices, beam indices, and equivalent channel magnitudes. The
    channel information can be obtained either from ray data stored in HDF5
    files or from imported Wireless InSite H-matrix files, depending on the
    configuration.

    For each processed episode, the function calls ``process_ep`` to generate
    the H-matrix, best beam index, and channel magnitude arrays. The outputs are
    then stacked across episodes and saved as compressed NumPy files in the
    beam output folder.

    Args:
        c: Runtime configuration object containing the working directory,
            output name, run range, episode settings, MIMO/codebook options,
            and H-matrix import flag.

    Returns:
        None. The generated arrays are saved to disk as:
            - ``hmatrix.npz`` containing the MIMO channel matrices;
            - ``beam_output.npz`` containing the selected beam indices;
            - ``channel_output.npz`` containing the equivalent channel magnitudes.

    Raises:
        FileNotFoundError: If required ray data files or H-matrix folders are
            missing.
        ValueError: If the generated output arrays cannot be stacked due to
            inconsistent shapes.
        OSError: If an input HDF5 file cannot be opened or an output file cannot
            be written.
    """
    
    output_beam_folder = os.path.join(
        c.working_directory, 
        'sim_data', 
        c.base_config.output_name, 'beams')
    if not os.path.exists(output_beam_folder):
        os.makedirs(output_beam_folder)
    output_beam_list = []
    output_channel_list = []
    output_hmatrix_list = []            
    
    if not c.import_hmatrix:
        database_folder = os.path.join(c.working_directory, 'sim_data', c.output_name, 'rays')
        max_runs = np.max(c.n_run)
        episodes=1
        
        if not c.isolated_sim:
            episodes = int((max_runs+1)/c.scenes_per_episode)
        
        for ep in range(episodes):
            print("Episode # ", ep)
            hmatrix,beamIndex, channel = process_ep(
                os.path.join(
                    database_folder, 
                    f'rays_ep{ep}.hdf5'), 
                    c)
            
            output_hmatrix_list.append(hmatrix)
            output_beam_list.append(beamIndex)
            output_channel_list.append(channel)
    else:
        hmatrix, beamIndex, channel = process_ep(None, c)
        
        output_hmatrix_list.append(hmatrix)
        output_beam_list.append(beamIndex)
        output_channel_list.append(channel)
                
    # Convert lists to numpy arrays
    output_hmatrix_matrix = np.stack(output_hmatrix_list,axis=0)
    output_beam_matrix = np.stack(output_beam_list,axis=0)
    output_channel_matrix = np.stack(output_channel_list,axis=0)
    
    # Save output
    hmatrixOutputFileName = os.path.join(output_beam_folder, 'hmatrix.npz')
    beamOutputFileName = os.path.join(output_beam_folder, 'beam_output.npz')
    channelOutputFileName = os.path.join(output_beam_folder, 'channel_output.npz')
    np.savez(hmatrixOutputFileName, hmatrix_array=output_hmatrix_matrix)
    np.savez(channelOutputFileName, channel_array=output_channel_matrix)
    np.savez(beamOutputFileName, beam_index_array=output_beam_matrix)
