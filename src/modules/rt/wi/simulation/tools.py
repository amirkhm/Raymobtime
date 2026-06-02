import numpy as np
import traci
import csv
import os
import platform

def pick_veh_from_area(veh_list, area_lim, n_veh, return_counts=False):
    """
    veh_list: id name from sumo of all cars
    area_lim: ((xmin, ymin), (xmax, ymax))
    n_veh: number of  vehicles to pick
    """
    min_x, min_y = area_lim[0]
    max_x, max_y = area_lim[1]
    veh_in_area = []
    for veh in veh_list:
        x, y = traci.vehicle.getPosition(veh)
        x, y = traci.simulation.convertGeo(x, y)
        if min_x <= x <= max_x and min_y <= y <= max_y:
            veh_in_area.append(veh)
    # Try to choose the number of vehicle in the area, if not enought vehicles return Non
    try:
        veh_chosen = np.random.choice(veh_in_area, n_veh, replace=False)
    except:
        if return_counts:
            return None, 0
        else:
            return None
    
    if return_counts:
        return veh_chosen, len(veh_in_area)

    return veh_chosen

def _get_csv_newline():
    """
    Avoid extra blank lines on Windows when using csv.writer.
    """
    return "" if platform.system() == "Windows" else None


def _as_ordered_index_dict(items):
    """
    Creates a dictionary preserving the original order of the input iterable.

    Example:
        ["veh3", "veh7"] -> {"veh3": 0, "veh7": 1}
    """
    if items is None:
        return {}

    return {
        item: idx
        for idx, item in enumerate(items)
    }


def _read_fixed_receivers_from_txrx(base_txrx_path, insite_rx_name):
    """
    Reads fixed receiver coordinates from base.txrx.

    Returns
    -------
    list[tuple]
        List of fixed receiver coordinates: [(x, y, z), ...]
    """
    receivers = []
    reading_rx_block = False
    remaining_vertices = 0

    with open(base_txrx_path, "r") as txrx_file:
        for line in txrx_file:
            line = line.strip()

            if f"begin_<points> {insite_rx_name}" in line:
                reading_rx_block = True
                continue

            if reading_rx_block and "nVertices" in line:
                remaining_vertices = int(line.split()[1])
                continue

            if reading_rx_block and remaining_vertices > 0:
                parts = line.split()

                if len(parts) >= 3:
                    x, y, z = parts[0], parts[1], parts[2]
                    receivers.append((x, y, z))

                remaining_vertices -= 1

                if remaining_vertices == 0:
                    break

    return receivers


def _write_fixed_receivers_rows(
    writer,
    episode_i,
    scene_i,
    base_insite_project_path,
    insite_rx_name,
):
    """
    Writes fixed receiver rows into the unified CSV file.

    Returns
    -------
    int
        Number of fixed receivers written.
    """
    base_txrx_path = os.path.join(base_insite_project_path, "base.txrx")
    fixed_receivers = _read_fixed_receivers_from_txrx(
        base_txrx_path,
        insite_rx_name,
    )

    for receiver_idx, (x, y, z) in enumerate(fixed_receivers):
        writer.writerow([
            episode_i,
            scene_i,
            "fixed_receiver",
            receiver_idx,
            -1,
            f"house{receiver_idx}",
            receiver_idx,
            "House",
            x,
            y,
            x,
            y,
            z,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ])

    return len(fixed_receivers)


def _write_vehicle_rows(
    c,
    writer,
    episode_i,
    scene_i,
    fixedReceivers,
    num_fixed_receivers,
    receiver_index_by_vehicle,
    transmitter_index_by_vehicle,
):
    """
    Writes SUMO vehicle rows into the unified CSV file.
    """
    for veh_i, veh in enumerate(traci.vehicle.getIDList()):
        x, y = traci.vehicle.getPosition(veh)
        angle = traci.vehicle.getAngle(veh)
        lane_id = traci.vehicle.getLaneID(veh)
        length = traci.vehicle.getLength(veh)
        width = traci.vehicle.getWidth(veh)
        height = traci.vehicle.getHeight(veh)
        speed = traci.vehicle.getSpeed(veh)
        x3, y3, z3 = traci.vehicle.getPosition3D(veh)
        type_id = traci.vehicle.getTypeID(veh)
        distance = traci.vehicle.getDistance(veh)
        wait_time = traci.vehicle.getWaitingTime(veh)

        xinsite, yinsite = traci.simulation.convertGeo(x, y)

        receiver_index = -1
        transmitter_index = -1

        if not fixedReceivers:
            receiver_index = receiver_index_by_vehicle.get(veh, -1)

        if c.V2V:
            transmitter_index = transmitter_index_by_vehicle.get(veh, -1)

        veh_output_index = veh_i + num_fixed_receivers if fixedReceivers else veh_i

        writer.writerow([
            episode_i,
            scene_i,
            "vehicle",
            receiver_index,
            transmitter_index,
            veh,
            veh_output_index,
            type_id,
            xinsite,
            yinsite,
            x3,
            y3,
            z3,
            lane_id,
            angle,
            speed,
            length,
            width,
            height,
            distance,
            wait_time,
        ])


def _write_pedestrian_rows(
    writer,
    episode_i,
    scene_i,
):
    """
    Writes SUMO pedestrian rows into the unified CSV file.
    """
    for ped_i, ped in enumerate(traci.person.getIDList()):
        x, y = traci.person.getPosition(ped)
        angle = traci.person.getAngle(ped)
        length = traci.person.getLength(ped)
        width = traci.person.getWidth(ped)
        speed = traci.person.getSpeed(ped)
        type_id = traci.person.getTypeID(ped)
        wait_time = traci.person.getWaitingTime(ped)

        xinsite, yinsite = traci.simulation.convertGeo(x, y)

        writer.writerow([
            episode_i,
            scene_i,
            "pedestrian",
            -1,
            -1,
            ped,
            ped_i,
            type_id,
            xinsite,
            yinsite,
            x,
            y,
            0,
            "",
            angle,
            speed,
            length,
            width,
            0,
            0,
            wait_time,
        ])


def writeSUMOInfoIntoFile(
    c,
    sumoOutputInfoFileName,
    episode_i,
    scene_i,
    lane_boundary_dict,
    veh_with_antenna,
    Tx_veh,
    fixedReceivers,
    use_pedestrians,
):
    """
    Save SUMO scene information into a single CSV file.

    This function writes vehicles, fixed receivers, transmitters and,
    optionally, pedestrians into the same CSV file.

    The column `object_class` identifies the row type:
        - vehicle
        - pedestrian
        - fixed_receiver

    The original order of `veh_with_antenna` and `Tx_veh` is preserved
    when assigning receiver and transmitter indices.
    """

    newline = _get_csv_newline()

    receiver_index_by_vehicle = _as_ordered_index_dict(veh_with_antenna)
    transmitter_index_by_vehicle = _as_ordered_index_dict(Tx_veh)

    header = [
        "episode_i",
        "scene_i",
        "object_class",
        "receiverIndex",
        "transmitterIndex",
        "object_id",
        "object_i",
        "typeID",
        "xinsite",
        "yinsite",
        "x3",
        "y3",
        "z3",
        "lane_id",
        "angle",
        "speed",
        "length",
        "width",
        "height",
        "distance",
        "waitTime",
        f"currentTime(ms)={traci.simulation.getCurrentTime()}",
        f"Ts(s)={c.sampling_interval}",
    ]

    with open(sumoOutputInfoFileName, "w", newline=newline) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)

        num_fixed_receivers = 0

        if fixedReceivers:
            num_fixed_receivers = _write_fixed_receivers_rows(
                writer=writer,
                episode_i=episode_i,
                scene_i=scene_i,
                base_insite_project_path=c.base_insite_project_path,
                insite_rx_name=c.insite_rx_name,
            )

        _write_vehicle_rows(
            c,
            writer=writer,
            episode_i=episode_i,
            scene_i=scene_i,
            fixedReceivers=fixedReceivers,
            num_fixed_receivers=num_fixed_receivers,
            receiver_index_by_vehicle=receiver_index_by_vehicle,
            transmitter_index_by_vehicle=transmitter_index_by_vehicle,
        )

        if use_pedestrians:
            _write_pedestrian_rows(
                writer=writer,
                episode_i=episode_i,
                scene_i=scene_i,
            )