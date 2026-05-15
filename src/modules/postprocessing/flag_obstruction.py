import os
import cv2
import json
import numpy as np
import pandas as pd

from raymobtime.src.modules.blensor.blensor_src import export_cam_info
from raw_data_handler import save5gmdata as fgdb
from raw_data_handler import global2pixels, gen_K
    
def obstruction_flag(c):

    main_folder = os.path.join(c.working_directory, 'sim_data', c.sim_name)
    if not os.path.exists(main_folder):
        raise FileNotFoundError(f"ERROR: folder {main_folder} not found")
    
    # csv_path = os.path.join(main_folder, 'CoordVehicleTxRx.csv')
    # if not os.path.exists(csv_path):
    #     raise FileNotFoundError(f"ERROR: csv file {csv_path} not found")
    # df = csv_to_df(csv_path, c.n_run)
    
    # refined_img_path = os.path.join(main_folder, 'refined_images')
    # if not os.path.exists(refined_img_path):
    #     os.makedirs(refined_img_path)

    database_path = os.path.join(main_folder, f'{c.sim_name}.db')
    session = fgdb.open_database(database_path)
    objcs = session.query(fgdb.InsiteObject)

    # Check for camera info
    cam_info_path = os.path.join(main_folder, 'blend_info', 'cam_info.json')
    if not os.path.exists(cam_info_path):
        export_cam_info() # Export and generate the json file
    with open(cam_info_path, 'r') as file:
        cam_info = json.load(file)
    cams = gen_K(cam_info)


    for ep_i, ep in enumerate(session.query(fgdb.Episode)):
        for sc_i, sc in enumerate(ep.scenes):
            rx_pos = []
            obstacles = []
            rx_obstacles = []
            for obj in sc.objects:
                rx_pos_cam = []
                obstacles_cam = []
                rx_obstacles_cam = []
                for cm in cams:
                    cam_position = np.array([cams[cm]["position"]["x"],
                                            cams[cm]["position"]["y"],
                                            cams[cm]["position"]["z"]])
                    vertices = []
                    for vert in obj.vertice_array:
                        _, pos = global2pixels(vert, 
                                                cam_position,
                                                cams[cm]["rotation_radians"]["z"],
                                                cams[cm]["rotation_radians"]["x"],
                                                cams[cm]["rotation_radians"]["y"],
                                                cams[cm]["K"])
                        vertices.append(pos)
                    
                    if len(obj.receivers) > 0:
                        position = obj.position.copy()
                        position[2] *= 2
                        _, pos = global2pixels(vert, 
                                                cam_position,
                                                cams[cm]["rotation_radians"]["z"],
                                                cams[cm]["rotation_radians"]["x"],
                                                cams[cm]["rotation_radians"]["y"],
                                                cams[cm]["K"])
                        rx_pos_cam.append(pos)
                        rx_obstacles_cam.append(vertices)
                    else:
                        obstacles_cam.append(vertices)
                if len(obj.receivers) > 0:
                    rx_pos.append(rx_pos_cam)
                    rx_obstacles.append(rx_obstacles_cam)
                else:
                    obstacles.append(obstacles_cam)
            obstacles = np.array(obstacles)
            rx_pos = np.array(rx_pos)
            rx_obstacles = np.array(rx_obstacles)
            np.savez('flag_obstruction.npz', receiver_position=rx_pos[0], obstacles=obstacles, receivers_as_obstacles=rx_obstacles[1:])
