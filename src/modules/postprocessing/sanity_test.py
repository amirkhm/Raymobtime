import os
import pandas as pd
import numpy as np
import h5py

def csv_check(main_folder):
    csv_file = os.path.join(main_folder, 'CoordVehicleTxRx.csv')
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
    main_folder = os.path.join(c.working_directory, 'sim_data', c.sim_name)
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)
    df, df_val = csv_check(main_folder)
    ray_check(main_folder, df_val)
    beam_check(main_folder, df_val)
    
    
