import csv
import numpy as np

def read_csv_sumo(file_name):
    scene_veh_info = {}
    with open(file_name, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if ('episode' in row[0]) or (len(row)==0):
                continue
            scene_veh_info[row[4]] = {
                'position':np.array([float(row[7]),
                                    float(row[8]),
                                    float(row[17])
                ]),
                'angle':angle_sumo2wi(float(row[13]))
            }
    return scene_veh_info

def angle_sumo2wi(angle):
    """
    convert angle from sumo to wireless insite
    sumo uses y+ ref clock-wize direction
    wi uses x+ ref anti-clock-wize direction
    """
    if angle<=-180:
        angle += 360
    if angle>180:
        angle -= 360

    angle = 90-angle
    
    if angle<=-180:
        angle += 360
    if angle>180:
        angle -= 360
    return angle
    