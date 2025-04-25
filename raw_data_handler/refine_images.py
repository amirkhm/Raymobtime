import os
import cv2
import json
import numpy as np
import pandas as pd

from blensor.blensor_src import export_cam_info

def global2pixels(Pob,Pcam,azimuth,elevation,K):
    """
    Convert a global coordinate to camera POV coordinate
    Inputs
    Pob: (x,y,z) global from object (X=front, Y=left, Z=up)
    Pcam: (x.y.z) global from camera
    azimuth: θ (radians, rotação em Z)
    K: camera parameters
    Output
    p_img: (pixels) x,y from image pixel
    p_c: (x,y,z) coordinate from camera POV
    """
    # Azimuth rotation matrix
    cos_phi = np.cos(azimuth)
    sin_phi = np.sin(azimuth)
    Rz = np.array([
        [cos_phi, -sin_phi, 0],
        [sin_phi,  cos_phi, 0],
        [0,          0,        1]
    ])

    # Elevation rotation matrix
    cos_theta = np.cos(elevation)
    sin_theta = np.sin(elevation)
    Ry = np.array([
        [cos_theta,  0, sin_theta],
        [0,        1,       0],
        [-sin_theta, 0, cos_theta]
    ])

    # Rotation Matrix
    R = np.dot(Ry, Rz.T)
    P_obj_cam = np.dot(R, Pob - Pcam)

    x_c = -P_obj_cam[1]   # -Y global turns to X from câmera (right+)
    y_c = -P_obj_cam[2]  # -Z global turns to Y from câmera (down+)
    z_c = P_obj_cam[0]   # X global turns to Z from câmera (depth+)
    
    if z_c <= 0:
        # raise ValueError("The object is behind the câmera!")
        return None, None #Object behind camera
    
    # Turns x,y,z from camera to pixels
    p_img = K @ np.array([x_c/z_c, y_c/z_c, 1])
    # u, v, _ = p_img
    return p_img[:2], np.array([x_c, y_c, z_c])

def gen_K(cam_info):
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

    main_folder = os.path.join(c.working_directory, 'sim_data', c.sim_name)
    if not os.path.exists(main_folder):
        raise FileNotFoundError(f"ERROR: folder {main_folder} not found")
    
    csv_path = os.path.join(main_folder, 'CoordVehicleTxRx.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"ERROR: csv file {csv_path} not found")
    df = csv_to_df(csv_path, c.n_run)
    
    refined_img_path = os.path.join(main_folder, 'refined_images')
    if not os.path.exists(refined_img_path):
        os.makedirs(refined_img_path)

    # Check for camera info
    cam_info_path = os.path.join(main_folder, 'blend_info', 'cam_info.json')
    if not os.path.exists(cam_info_path):
        export_cam_info() # Export and generate the json file
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

                cam_position = np.array([cam_info[cam_name]["position"]["x"],
                                         cam_info[cam_name]["position"]["y"],
                                         cam_info[cam_name]["position"]["z"]])
                pixels, p_cam = global2pixels(position_Rx, 
                                              cam_position,
                                              cam_info[cam_name]["angles"]["azimuth"], 
                                              cam_info[cam_name]["angles"]["elevation"],
                                              cam_info[cam_name]["K"])
                img_window_size = np.array([cam_info[cam_name]["pixel_resolution"]["width"],
                                            cam_info[cam_name]["pixel_resolution"]["height"]])
                if not obj_in_cam_view(pixels, img_window_size):
                    continue
                rf_img_marked = cv2.circle(img_raw, pixels.astype(int), 3, (0,0,255), -1)
                rf_img_marked_path = os.path.join(bs_rf_path, 'marker', f'run{run}', f"Camera{cam}.png")
                cv2.imwrite(rf_img_marked_path, rf_img_marked)
                bs_veh_positions[row["EpisodeID"], row["SceneID"], row["RxID"], cam, :] = p_cam
    
    if c.sim_BS_img:
        np.savez(os.path.join(bs_rf_path, 'RxPosCamraPOV.npz'), position=bs_veh_positions)
                    
                

                    