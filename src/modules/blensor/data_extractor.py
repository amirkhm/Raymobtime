import argparse
import json
import os
import sys

import bpy


def parse_script_arguments():
    """
    Parse arguments passed to this script after Blender's ``--`` separator.

    Returns:
        argparse.Namespace: Parsed command-line arguments containing the path
        to the temporary runtime configuration file.
    """

    if "--" in sys.argv:
        script_args = sys.argv[sys.argv.index("--") + 1:]
    else:
        script_args = []

    parser = argparse.ArgumentParser(
        description="Export Blensor camera information."
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to the temporary Blensor runtime configuration JSON.",
    )

    return parser.parse_args(script_args)

def get_camera_details(camera_name):
    """
        Extract camera position, rotation, and optical properties.

        Args:
            camera_name: Name of the Blender camera object.

        Returns:
            dict: Camera information that can be serialized to JSON.

        Raises:
            KeyError: If the camera does not exist in the Blender scene.
            TypeError: If the named object is not a camera.
    """
    
    camera_object = bpy.data.objects.get(camera_name)

    if camera_object is None:
        raise KeyError(
            "Camera object '{}' was not found.".format(camera_name)
        )

    if camera_object.type != "CAMERA":
        raise TypeError(
            "Object '{}' is not a camera.".format(camera_name)
        )

    camera_data = camera_object.data
    scene = bpy.context.scene

    resolution_percentage = scene.render.resolution_percentage / 100.0
    resolution_width = int(
        scene.render.resolution_x * resolution_percentage
    )
    resolution_height = int(
        scene.render.resolution_y * resolution_percentage
    )

    return {
        "name": camera_name,

        "location": {
            "x": float(camera_object.location.x),
            "y": float(camera_object.location.y),
            "z": float(camera_object.location.z),
        },

        "rotation_euler": {
            "x": float(camera_object.rotation_euler.x),
            "y": float(camera_object.rotation_euler.y),
            "z": float(camera_object.rotation_euler.z),
        },

        "focal_length_mm": float(camera_data.lens),

        "sensor_size_mm": {
            "width": float(camera_data.sensor_width),
            "height": float(camera_data.sensor_height),
        },

        "pixel_resolution": {
            "width": resolution_width,
            "height": resolution_height,
        },

        "clip_start": float(camera_data.clip_start),
        "clip_end": float(camera_data.clip_end),
    }

def export_camera_info(config_path):
    """
    Read the temporary runtime configuration and export camera information.

    Args:
        config_path: Path to the temporary JSON configuration file.

    Returns:
        str: Path to the generated ``cam_info.json`` file.
    """

    with open(config_path, "r", encoding="utf-8") as file:
        cfg = json.load(file)

    n_cameras = int(cfg["blensor"]["n_camera_BS"])

    data_info_path = os.path.join(
        cfg["paths"]["postprocessed_dir"],
        "blend_info",
    )

    os.makedirs(data_info_path, exist_ok=True)

    cameras_info = {}

    for cam_index in range(n_cameras):
        camera_name = "Camera{}".format(cam_index)
        cameras_info[camera_name] = get_camera_details(camera_name)

    output_path = os.path.join(
        data_info_path,
        "cam_info.json",
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(cameras_info, file, indent=4)

    return output_path


def main():
    """
    Execute camera information extraction and remove the temporary config.
    """

    args = parse_script_arguments()
    config_path = os.path.abspath(args.config)

    try:
        output_path = export_camera_info(config_path)

        print(
            "Camera information exported successfully to: {}".format(
                output_path
            )
        )

    finally:
        if os.path.isfile(config_path):
            try:
                os.remove(config_path)
                print(
                    "Temporary configuration removed: {}".format(
                        config_path
                    )
                )
            except OSError as exc:
                print(
                    "Warning: could not remove temporary configuration "
                    "'{}': {}".format(config_path, exc)
                )


if __name__ == "__main__":
    main()