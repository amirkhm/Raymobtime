import os
import bpy
import math
import json

def get_camera_details(camera_name="Camera"):
    """
    Extracts camera details (position, rotation, focal length, sensor size, etc.).
    Args:
        camera_name (str): Name of the camera object in Blender (default: "Camera").
    Returns:
        dict: Camera metadata.
    OBS:
        azimuth and elevation are considering a different POV from the blender
        that will be used in the conversion to pixels
        POV:{
            x+: front,
            y+: left,
            z+: up
        }
    """
    if camera_name not in bpy.data.objects:
        raise ValueError(f"Camera '{camera_name}' not found in the scene.")

    cam = bpy.data.objects[camera_name]
    cam_data = cam.data

    # Convert rotation from radians to degrees
    rotation_degrees = (
        math.degrees(cam.rotation_euler.x),
        math.degrees(cam.rotation_euler.y),
        math.degrees(cam.rotation_euler.z)
    )

    # Get render resolution (window/sensor size)
    render = bpy.context.scene.render
    resolution_x = render.resolution_x
    resolution_y = render.resolution_y

    camera_details = {
        "name": cam.name,
        "position": {
            "x": cam.location.x,
            "y": cam.location.y,
            "z": cam.location.z,
        },
        "rotation_radians": {
            "x": cam.rotation_euler.x,
            "y": cam.rotation_euler.y,
            "z": cam.rotation_euler.z,
        },
        "rotation_degrees": {
            "x": rotation_degrees[0],
            "y": rotation_degrees[1],
            "z": rotation_degrees[2],
        },
        "angles":{
            "azimuth":rotation_degrees[2]+90,
            "elevation":-rotation_degrees[0]+180
        },
        "focal_length_mm": cam_data.lens,
        "sensor_size_mm": {
            "width": cam_data.sensor_width,
            "height": cam_data.sensor_height,
        },
        "pixel_resolution": {
            "width": resolution_x,
            "height": resolution_y,
        },
        "clip_range": {
            "near": cam_data.clip_start,
            "far": cam_data.clip_end,
        },
    }

    return camera_details

if __name__ == "__main__":

    with open('config.json', 'r') as file:
        cfg = json.load(file)

    cur_dir = os.curdir
    n_cameras = cfg['blensor_options']['img_simulation_options']['n_camera_BS']
    data_info_path = os.path.join(cur_dir, 'sim_data', cfg['simulation_paths']['results_dir_path'], 'blend_info')
    if not os.path.exists(data_info_path):
        os.makedirs(data_info_path)

    cameras_info = {}
    for cam in range(n_cameras):
        cam_name = f"Camera{cam}"
        cam_info = get_camera_details(cam_name)
        cameras_info[cam_name] = cam_info
    
    with open(os.path.join(data_info_path, 'cam_info.json'), 'w') as file:
        json.dump(cameras_info, file, indent=4)
    