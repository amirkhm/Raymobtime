import os
import cv2
import json
import numpy as np
import pandas as pd

from src.modules.blensor.blensor_src import export_cam_info
from src.modules.data_processing import save5gmdata as fgdb

def global2pixels(Pob, Pcam, yaw, roll, pitch, K):
    """
    Project a 3D global point into image pixel coordinates.

    This function converts a point from the global coordinate system to the
    camera coordinate system using the camera position and Euler rotations.
    The transformed point is then projected into the image plane using the
    intrinsic camera matrix.

    Args:
        Pob: Object position in global coordinates as an array-like object
            ``[x, y, z]``.
        Pcam: Camera position in global coordinates as an array-like object
            ``[x, y, z]``.
        yaw: Camera rotation around the global z-axis, in radians.
        roll: Camera rotation around the global x-axis, in radians.
        pitch: Camera rotation around the global y-axis, in radians.
        K: Camera intrinsic matrix.

    Returns:
        A tuple containing:
            - p_img: Pixel coordinates ``[u, v]`` if the object is in front of
              the camera, otherwise ``None``.
            - p_c: Object coordinates in the camera reference frame.

    Notes:
        If the projected point is behind the camera, the function returns
        ``None`` for the image pixel coordinates.
    """

    rel_pos = Pob - Pcam

    # Z rotation
    cos_phi = np.cos(yaw)
    sin_phi = np.sin(yaw)
    Rz = np.array([
    [cos_phi, -sin_phi, 0],
    [sin_phi, cos_phi, 0],
    [0, 0, 1]
    ])

    # Y rotation
    cos_theta = np.cos(pitch)
    sin_theta = np.sin(pitch)
    Ry = np.array([
    [cos_theta, 0, sin_theta],
    [0, 1, 0],
    [-sin_theta, 0, cos_theta]
    ])

    # X Rotation
    cos_phi = np.cos(roll)
    sin_phi = np.sin(roll)
    Rx = np.array([
    [1, 0, 0],
    [0, cos_phi, -sin_phi],
    [0, sin_phi, cos_phi]
    ])

    # Rotation Matrix
    R = Rz @ Ry @ Rx
    P_obj_cam = np.dot(R.T, rel_pos)

    #Blender camera inittialy points to z-
    x_c = P_obj_cam[0]  # X global turns to X from câmera (right+)
    y_c = -P_obj_cam[1] #-Z global turns to Y from câmera (down+)
    z_c = -P_obj_cam[2]  # Y global turns to Z from câmera (depth+)
    
    if z_c <= 0:
        # raise ValueError("The object is behind the câmera!")
        return None, np.array([x_c, y_c, z_c]) #Object behind camera
    
    # Turns x,y,z from camera to pixels
    p_img = K @ np.array([x_c/z_c, y_c/z_c, 1])
    return p_img[:2], np.array([x_c, y_c, z_c])

def gen_K(cam_info):
    """
    Generate intrinsic camera matrices from camera metadata.

    This function computes the intrinsic matrix ``K`` for each camera using its
    focal length, sensor size, and image resolution. The resulting matrix is
    added to each camera entry in the input dictionary.

    Args:
        cam_info: Dictionary containing camera metadata. Each camera entry must
            include focal length, pixel resolution, and sensor size.

    Returns:
        The updated camera information dictionary with an added ``K`` matrix for
        each camera.

    Raises:
        KeyError: If required camera metadata fields are missing.
    """
    for cam_name in cam_info:
        cam = cam_info[cam_name]
        fx = cam["focal_length_mm"]*cam["pixel_resolution"]["width"]/cam["sensor_size_mm"]["width"]
        fy = cam["focal_length_mm"]*cam["pixel_resolution"]["height"]/cam["sensor_size_mm"]["height"]
        cx = cam["pixel_resolution"]["width"]/2
        cy = cam["pixel_resolution"]["height"]/2
        K = np.array([[fx, 0, cx],
                [0, fy, cy],
                [0, 0, 1]])
        cam["K"] = K
    return cam_info

def csv_to_df(csv_file, range_runs):
    """
    Load and filter receiver coordinate data from a CSV file.

    This function reads a coordinate CSV file, computes the run index from the
    episode and scene identifiers, keeps only valid entries, and filters the
    dataframe to the requested run range.

    Args:
        csv_file: Path to the coordinate CSV file.
        range_runs: Iterable containing the run indices that should be kept.

    Returns:
        A pandas DataFrame containing only valid rows within the selected run
        range. A new ``Run`` column is added to the dataframe.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        KeyError: If required columns such as ``EpisodeID``, ``SceneID``, or
            ``Val`` are missing.
    """
    df = pd.read_csv(csv_file)
    episodes = df["EpisodeID"].values
    scenes = df["SceneID"].values
    scenes_max = max(df["SceneID"].values)+1
    runs = episodes*scenes_max + scenes
    df["Run"] = runs
    df = df[df["Val"] == "V"]
    df = df[df["Run"].isin(range_runs)]
    return df

def obj_in_cam_view(pixel, window_size):
    """
    Check if an object and pixels are within the camera POV
    Input:
        pixel: u,v (pixels) where the object is located in the cam
        window_size: x,y (pixels) size in pixels of the image taken from camera
    Output:
        check: (boolean) True for object in camera POV
    """
    if np.sum(pixel) == None:
        return False # object behind camera
    return (0 <= pixel[0] < window_size[0]) and (0 <= pixel[1] < window_size[1])
    
def image_refinement(c):
    """
    Refine generated images by marking receiver positions and bounding boxes.

    This function processes raw Blensor images and receiver metadata to generate
    refined image datasets. For each valid receiver in the selected simulation
    runs, the receiver position is projected into each configured Base Station
    camera view. If the receiver is visible, the function saves a marked image
    with the projected receiver point and another image with a bounding box
    around the corresponding vehicle object.

    The function also stores receiver positions in the camera coordinate system
    as a NumPy ``.npz`` file.

    Args:
        c: Runtime configuration object containing simulation paths, output
            name, run range, camera options, and Blensor image settings.

    Returns:
        None. Refined images and receiver camera-frame positions are saved to
        disk.

    Raises:
        FileNotFoundError: If the main simulation folder or coordinate CSV file
            does not exist.
        KeyError: If required camera metadata, CSV columns, or database fields
            are missing.
        ValueError: If vehicle vertices cannot be projected or converted into a
            valid bounding box.
    """

    main_folder = c.result_dir_processed_data
    if not os.path.exists(main_folder):
        raise FileNotFoundError(f"ERROR: folder {main_folder} not found")
    
    csv_path = os.path.join(main_folder, 'CoordVehicleTxRx.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"ERROR: csv file {csv_path} not found")
    df = csv_to_df(csv_path, c.n_run)
    
    refined_img_path = os.path.join(
        c.results_dir_postprocessed, 
        'refined_images')
    if not os.path.exists(refined_img_path):
        os.makedirs(refined_img_path)

    database_path = os.path.join(
        main_folder, 
        f'{c.base_config.output_name}.db')
    session = fgdb.open_database(database_path)
    objcs = session.query(fgdb.InsiteObject)

    # Check for camera info
    cam_info_path = os.path.join(
        main_folder, 
        'blend_info', 
        'cam_info.json')   
    if not os.path.exists(cam_info_path):
        export_cam_info(c) # Export and generate the json file       
    with open(cam_info_path, 'r') as file:
        cam_info = json.load(file)
    cam_info = gen_K(cam_info)

    if c.sim_BS_img:
        bs_rf_path = os.path.join(main_folder, "refined_images", "BS")
        if not os.path.exists(bs_rf_path):
            os.makedirs(bs_rf_path)
        episodes = max(df["EpisodeID"].values)+1
        scenes = max(df["SceneID"].values)+1
        rxs = max(df["RxID"].values)+1
        bs_veh_positions = np.ones((episodes,scenes,rxs,c.n_cameras_blensor_scenario, 3))*np.nan

    for index, row in df.iterrows():
        run = row["Run"]
        position_Rx = np.array([row["x"],row["y"],row["z"]])
        if c.sim_BS_img:
            # Refine BS images
            raw_dt_path = os.path.join(main_folder, 'images', 'BS', f'run{run}')
            for cam in range(c.n_cameras_blensor_scenario):
                cam_name = f'Camera{cam}'
                img_raw_path = os.path.join(raw_dt_path, f'{cam_name}.png')
                img_raw = cv2.imread(img_raw_path)

                cam_position = np.array([cam_info[cam_name]["location"]["x"],
                                         cam_info[cam_name]["location"]["y"],
                                         cam_info[cam_name]["location"]["z"]])
                pixels, p_cam = global2pixels(position_Rx, 
                                              cam_position,
                                              cam_info[cam_name]["rotation_euler"]["z"],
                                              cam_info[cam_name]["rotation_euler"]["x"],
                                              cam_info[cam_name]["rotation_euler"]["y"],
                                              cam_info[cam_name]["K"])
                img_window_size = np.array([cam_info[cam_name]["pixel_resolution"]["width"],
                                            cam_info[cam_name]["pixel_resolution"]["height"]])

                rf_img_marked_path = os.path.join(bs_rf_path, 'marker', f'run{run}', f'rx_{row["RxID"]}')
                if not os.path.exists(rf_img_marked_path):
                    os.makedirs(rf_img_marked_path)
                rf_img_bb_path = os.path.join(bs_rf_path, 'bb', f'run{run}', f'rx_{row["RxID"]}')
                if not os.path.exists(rf_img_bb_path):
                    os.makedirs(rf_img_bb_path)
                
                if not obj_in_cam_view(pixels, img_window_size):
                    cv2.imwrite(os.path.join(rf_img_marked_path, f"Camera{cam}.png"), img_raw)
                    cv2.imwrite(os.path.join(rf_img_bb_path, f"Camera{cam}.png"), img_raw)
                else:
                    rf_img_marked = cv2.circle(img_raw.copy(), pixels.astype(int), 3, (0,255,0), -1)
                    cv2.imwrite(os.path.join(rf_img_marked_path, f"Camera{cam}.png"), rf_img_marked)

                    obj = objcs.filter_by(name=row['VehicleName']).all()
                    if len(obj) > 1:
                        for veh in objcs.filter_by(name=row['VehicleName']):
                            if np.prod(np.isclose(veh.position[:2], position_Rx[:2], rtol=1e-15, atol=1e-15)):
                                obj = veh
                    else:
                        obj = obj[0]
                    vertices = []
                    for vertc in obj.vertice_array:
                        pixels, _ = global2pixels(vertc, 
                                                cam_position,
                                                cam_info[cam_name]["rotation_radians"]["z"],
                                                cam_info[cam_name]["rotation_radians"]["x"],
                                                cam_info[cam_name]["rotation_radians"]["y"],
                                                cam_info[cam_name]["K"])
                        if obj_in_cam_view(pixels, img_window_size):
                            vertices.append(pixels)
                    
                    vertices = np.array(vertices)
                    del obj
                    vertices_max = np.max(vertices,axis=0)
                    vertices_min = np.min(vertices,axis=0)

                    rf_img_bb = cv2.rectangle(img_raw.copy(), tuple(vertices_min.astype(int)), tuple(vertices_max.astype(int)), (0,255,0),2)
                    cv2.imwrite(os.path.join(rf_img_bb_path, f"Camera{cam}.png"), rf_img_bb)

                bs_veh_positions[row["EpisodeID"], row["SceneID"], row["RxID"], cam, :] = p_cam
            print(f"Refined images from run {run:5d} and Rx {row['RxID']:2d}")
    
    if c.sim_BS_img:
        np.savez(os.path.join(bs_rf_path, 'RxPosCamraPOV.npz'), position=bs_veh_positions)