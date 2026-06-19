import numpy as np
import traci
import csv
import os
import platform

def pick_veh_from_area(veh_list, area_lim, n_veh, return_counts=False):
    """
    Select vehicles located inside a rectangular area.

    This function checks the current SUMO position of each vehicle, converts it
    to the Wireless InSite coordinate system, filters vehicles inside the given
    area limits, and randomly selects the requested number of vehicles.

    Args:
        veh_list: List of SUMO vehicle identifiers.
        area_lim: Area limits defined as ``((xmin, ymin), (xmax, ymax))``.
        n_veh: Number of vehicles to randomly select from the area.
        return_counts: If ``True``, also return the number of vehicles found
            inside the area. Defaults to ``False``.

    Returns:
        If ``return_counts`` is ``False``, returns an array with the selected
        vehicle IDs or ``None`` if there are not enough vehicles.
        If ``return_counts`` is ``True``, returns a tuple containing the selected
        vehicle IDs and the number of vehicles inside the area. If there are not
        enough vehicles, returns ``(None, 0)``.
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
    Return the newline parameter used when writing CSV files.

    This helper avoids extra blank lines on Windows when using ``csv.writer``.

    Returns:
        An empty string on Windows, otherwise ``None``.
    """
    return "" if platform.system() == "Windows" else None


def _as_ordered_index_dict(items):
    """
    Create an index dictionary while preserving the input order.

    This function maps each item to its position in the original iterable. It is
    used to preserve the original receiver and transmitter ordering when writing
    SUMO metadata to CSV.

    Args:
        items: Iterable of item identifiers, or ``None``.

    Returns:
        A dictionary mapping each item to its original index. If ``items`` is
        ``None``, returns an empty dictionary.
    """
    if items is None:
        return {}

    return {
        item: idx
        for idx, item in enumerate(items)
    }


def _read_fixed_receivers_from_txrx(base_txrx_path, insite_rx_name):
    """
    Read fixed receiver coordinates from a Wireless InSite TX/RX file.

    This function searches for the receiver points block identified by
    ``insite_rx_name`` in a ``base.txrx`` file, reads the declared vertices, and
    returns their coordinates.

    Args:
        base_txrx_path: Path to the Wireless InSite ``base.txrx`` file.
        insite_rx_name: Name of the receiver points block to read.

    Returns:
        A list of fixed receiver coordinates as ``[(x, y, z), ...]``.

    Raises:
        FileNotFoundError: If the TX/RX file does not exist.
        ValueError: If the ``nVertices`` value cannot be converted to an integer.
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
    Write fixed receiver rows to the unified SUMO information CSV file.

    This function reads fixed receiver coordinates from ``base.txrx`` and writes
    one CSV row for each receiver using the ``fixed_receiver`` object class.

    Args:
        writer: CSV writer object used to write rows.
        episode_i: Episode index associated with the current scene.
        scene_i: Scene index associated with the current scene.
        base_insite_project_path: Path to the base Wireless InSite project
            folder.
        insite_rx_name: Name of the receiver points block in ``base.txrx``.

    Returns:
        Number of fixed receiver rows written to the CSV file.
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
    Write SUMO vehicle rows to the unified CSV file.

    This function iterates over the current SUMO vehicles, extracts mobility and
    geometric information through TraCI, converts vehicle positions to Wireless
    InSite coordinates, assigns receiver and transmitter indices when
    applicable, and writes the vehicle metadata to the CSV file.

    Args:
        c: Runtime configuration object containing V2V and simulation settings.
        writer: CSV writer object used to write rows.
        episode_i: Episode index associated with the current scene.
        scene_i: Scene index associated with the current scene.
        fixedReceivers: Whether the simulation uses fixed receivers.
        num_fixed_receivers: Number of fixed receivers already written to the
            CSV file.
        receiver_index_by_vehicle: Dictionary mapping receiver vehicle IDs to
            receiver indices.
        transmitter_index_by_vehicle: Dictionary mapping transmitter vehicle IDs
            to transmitter indices.

    Returns:
        None.
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
    Write SUMO pedestrian rows to the unified CSV file.

    This function iterates over the current SUMO pedestrians, extracts their
    position, orientation, size, speed, type, and waiting time through TraCI,
    converts their coordinates to the Wireless InSite coordinate system, and
    writes them to the CSV file using the ``pedestrian`` object class.

    Args:
        writer: CSV writer object used to write rows.
        episode_i: Episode index associated with the current scene.
        scene_i: Scene index associated with the current scene.

    Returns:
        None.
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
    Save SUMO scene information to a unified CSV file.

    This function writes metadata from the current SUMO scene into a single CSV
    file. The output can include vehicles, fixed receivers, transmitters, and
    optionally pedestrians. The ``object_class`` column identifies the type of
    each row.

    Receiver and transmitter indices preserve the original order of
    ``veh_with_antenna`` and ``Tx_veh``.

    Args:
        c: Runtime configuration object containing simulation timing, V2V
            settings, base Wireless InSite paths, and receiver names.
        sumoOutputInfoFileName: Path to the CSV file to be written.
        episode_i: Episode index associated with the current scene.
        scene_i: Scene index associated with the current scene.
        lane_boundary_dict: Lane boundary information. Currently not used
            directly by this function.
        veh_with_antenna: Iterable containing vehicles selected as receivers.
        Tx_veh: Iterable containing vehicles selected as transmitters, or
            ``None`` when V2V mode is disabled.
        fixedReceivers: Whether fixed receivers should be written from
            ``base.txrx``.
        use_pedestrians: Whether pedestrian rows should be included.

    Returns:
        None. The CSV file is written to ``sumoOutputInfoFileName``.

    Raises:
        FileNotFoundError: If fixed receivers are enabled and ``base.txrx`` is
            not found.
        OSError: If the output CSV file cannot be written.
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
        f"currentTime(ms)={traci.simulation.getTime()}",
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