import csv
import numpy as np

def read_csv_sumo(file_name):
    """
    Read vehicle position and orientation data from a SUMO CSV file.

    This function parses a SUMO output CSV file and builds a dictionary indexed
    by vehicle identifier. For each vehicle, it stores the 3D position and the
    orientation angle converted from the SUMO reference convention to the
    Wireless InSite reference convention.

    Args:
        file_name: Path to the SUMO CSV file to be read.

    Returns:
        A dictionary indexed by vehicle ID. Each entry contains:
            - ``position``: NumPy array with the vehicle x, y, and z coordinates.
            - ``angle``: Vehicle orientation angle converted to the Wireless
              InSite convention.

    Raises:
        FileNotFoundError: If the input CSV file does not exist.
        IndexError: If a CSV row does not contain the expected number of fields.
        ValueError: If position or angle values cannot be converted to floats.
    """
    scene_veh_info = {}
    with open(file_name, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if ('episode' in row[0]) or (len(row)==0):
                continue
            scene_veh_info[row[5]] = {
                'position':np.array([float(row[8]),
                                    float(row[9]),
                                    float(row[18])
                ]),
                'angle':angle_sumo2wi(float(row[14]))
            }
    return scene_veh_info

def angle_sumo2wi(angle):
    """
    Convert an orientation angle from SUMO convention to Wireless InSite convention.

    SUMO uses the positive y-axis as reference and clockwise rotation direction,
    while Wireless InSite uses the positive x-axis as reference and
    counterclockwise rotation direction. This function normalizes the input angle
    to the interval [-180, 180], applies the convention conversion, and normalizes
    the result again.

    Args:
        angle: Orientation angle in degrees using the SUMO convention.

    Returns:
        Orientation angle in degrees using the Wireless InSite convention.
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
    