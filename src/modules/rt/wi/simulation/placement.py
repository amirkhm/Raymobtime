import copy
import os
import numpy as np
import traci
from src.modules.rt.wi.modeling import (
    errors, 
    objects)

def place_by_sumo(
        c,
        antenna, 
        antenna_Tx, 
        car_material_id, 
        lane_boundary_dict, 
        veh_with_antenna, 
        Tx_veh=None, 
        V2V=False, 
        fixed_receivers=False, 
        use_pedestrians=False):
    """
    Place SUMO vehicles and pedestrians into a Wireless InSite structure group.

    This function reads the current SUMO simulation state through TraCI,
    converts vehicle and pedestrian positions to Wireless InSite coordinates,
    creates rectangular prism representations for each object, and places
    receiver and transmitter antennas on the selected vehicles.

    When detailed vehicle templates are enabled in the configuration, the
    function also generates the serialized object geometry string using the
    corresponding vehicle or pedestrian model files.

    Args:
        c: Runtime configuration object containing simulation settings, template
            options, geographic reference information, and asset paths.
        antenna: Receiver antenna vertex list template. It is copied and cleared
            before receiver positions are inserted.
        antenna_Tx: Transmitter antenna vertex list template. Used only in V2V
            mode.
        car_material_id: Material identifier used for generated rectangular
            prism vehicles and pedestrians.
        lane_boundary_dict: Lane boundary information. Currently not used
            directly by this function.
        veh_with_antenna: Iterable containing vehicle IDs that should receive
            receiver antennas.
        Tx_veh: Iterable containing vehicle IDs that should receive transmitter
            antennas in V2V mode. Defaults to ``None``.
        V2V: Whether to place transmitter antennas on vehicles. Defaults to
            ``False``.
        fixed_receivers: Whether the scenario uses fixed receivers instead of
            vehicle-mounted receivers. Defaults to ``False``.
        use_pedestrians: Whether to include SUMO pedestrians in the generated
            Wireless InSite object group. Defaults to ``False``.

    Returns:
        A tuple containing:
            - structure_group: Wireless InSite structure group with generated
              vehicles and pedestrians.
            - antenna: Receiver antenna vertex list, or ``None`` when not
              applicable.
            - antenna_Tx: Transmitter antenna vertex list, or ``None`` when not
              applicable.
            - all_vehicles: Serialized detailed vehicle geometry when templates
              are enabled, otherwise an empty string.

        If no required antenna vehicle is present, the function returns
        ``(None, None, None, None)``.
    """

    antenna = copy.deepcopy(antenna)
    antenna.clear()
    if V2V:
        antenna_Tx = copy.deepcopy(antenna_Tx)
        antenna_Tx.clear()

    structure_group = objects.StructureGroup()
    structure_group.name = 'SUMO cars'

    str_vehicles = ''
    veh_i = None
    c_present = False
    c_tx_present = False

    if use_pedestrians:
        for ped_i, ped in enumerate(traci.person.getIDList()):
            (
                (x, y),
                angle,
                length,
                width,
                pedestrian_type,
            ) = [f(ped) for f in [
                traci.person.getPosition,
                traci.person.getAngle,
                traci.person.getLength,
                traci.person.getWidth,
                traci.person.getTypeID,
            ]]

            xinsite, yinsite = traci.simulation.convertGeo(x, y)
            pedestrian = objects.RectangularPrism(length, width, 1.72, material=car_material_id)
            pedestrian.translate((-length/2, -width/2, 0))
            pedestrian.rotate(90-angle) #use 90 degrees - angle to convert from y to x-axis the reference

            thisAngleInRad = np.radians(angle) #*np.pi/180
            deltaX = (length/2.0) * np.sin(thisAngleInRad)
            deltaY = (length/2.0) * np.cos(thisAngleInRad)
            pedestrian.translate((xinsite-deltaX, yinsite-deltaY, 0)) #now can translate

            pedestrian_structure = objects.Structure(name=ped)
            pedestrian_structure.add_sub_structures(pedestrian)
            structure_group.add_structures(pedestrian_structure)

            # 1.72 size of a perdestrian
            if c.vehicles_template:
                str_vehicles = get_model(
                    c=c,
                    str_vehicles=str_vehicles,
                    name=ped,
                    model_type=pedestrian_type,
                    x=xinsite - deltaX,
                    y=yinsite - deltaY,
                    z=0,
                    angle=90 - angle,
                    height=1.72,
                    length=length,
                    width=width,
                ) 

    for veh_i, veh in enumerate(traci.vehicle.getIDList()):
        (
            (x, y),
            (x3, y3, z3),
            angle,
            lane_id,
            length,
            width,
            height,
            vehicle_type,
        ) = [f(veh) for f in [
            traci.vehicle.getPosition,
            traci.vehicle.getPosition3D,
            traci.vehicle.getAngle,
            traci.vehicle.getLaneID,
            traci.vehicle.getLength,
            traci.vehicle.getWidth,
            traci.vehicle.getHeight,
            traci.vehicle.getTypeID,
        ]]
        
        x, y = traci.simulation.convertGeo(x, y)

        #the prism is draw using the first coordinate aligned with x, then y and z. Length is initially along x
        #and later the object will be rotates
        car = objects.RectangularPrism(length, width, height, material=car_material_id)

        #for proper rotation, first centralize the object on plane xy
        car.translate((-length/2, -width/2, 0))
        #now can rotate, but note SUMO assumes y-axis as the reference, and angle increases towards x-axis,
        #while we assume angles start from x-axis in our rotate method (see https://en.wikipedia.org/wiki/Rotation_matrix)
        car.rotate(90-angle) #use 90 degrees - angle to convert from y to x-axis the reference

        #SUMO reports position of middle of front bumper. We need to reposition to the middle of the vehicle
        #for that, use the angle to find to where the vehicle is facing and then translate
        thisAngleInRad = np.radians(angle) #*np.pi/180
        deltaX = (length/2.0) * np.sin(thisAngleInRad)
        deltaY = (length/2.0) * np.cos(thisAngleInRad)

        if c.drone_simulation:        
            is_drone = veh.startswith("droneFlow")

            if is_drone:
                drone_altitude = getattr(c, "drone_altitude", 10.0)
                z_obj = z3 + drone_altitude
        else:
                z_obj = z3        

        car.translate((x-deltaX, y-deltaY, z_obj)) #now can translate

        car_structure = objects.Structure(name=veh)
        car_structure.add_sub_structures(car)
        structure_group.add_structures(car_structure)

        if c.vehicles_template:
            str_vehicles = get_model(
                c=c,
                str_vehicles=str_vehicles,
                name=veh,
                model_type=vehicle_type,
                x=x - deltaX,
                y=y - deltaY,
                z=z_obj,
                angle=90 - angle,
                height=height,
                length=length,
                width=width,
            ) 

        is_drone = str(vehicle_type).strip().lower() == "drone"

        antenna_x = x - deltaX
        antenna_y = y - deltaY

        if is_drone:
            antenna_z = z_obj - 0.1
        else:
            antenna_z = z_obj + height + 0.1

        # Receiver antenna
        if veh in veh_with_antenna:
            if is_drone and not c.drone_simulation:
                # Drone must not be used as a receiver when drone simulation is disabled.
                pass
            else:
                antenna.add_vertice((
                    antenna_x,
                    antenna_y,
                    antenna_z,
                ))
                c_present = True

        # Transmitter antenna
        if V2V and veh in Tx_veh:
            if is_drone and not c.drone_simulation:
                # Drone must not be used as a transmitter when drone simulation is disabled.
                pass
            else:
                antenna_Tx.add_vertice((
                    antenna_x,
                    antenna_y,
                    antenna_z,
                ))
                c_tx_present = True

    if c.vehicles_template:
        from src.modules.rt.wi.modeling import vehicles_template as vt

        all_vehicles = str(
            vt.vehicles_template(
                searchList=[
                    {
                        "a": str_vehicles,
                        "long": c.longitude,
                        "lat": c.latitude,
                    }
                ]
            )
        )
    else:
        all_vehicles = ""

    if fixed_receivers:
        return structure_group, None, None, all_vehicles

    if not c_present: #there are no vehicles with antennas
        return None, None, None, None

    if not c_tx_present and V2V: #there are no vehicles with antennas
        return None, None, None, None

    if veh_i is None: #there are no vehicles in the scene according to SUMO (traci)
        return None, None, None, None

    return structure_group, antenna, antenna_Tx, all_vehicles

def place_on_line(
        origin_array, 
        destination_list, 
        dim_list, 
        space, 
        object,
        antenna=None, 
        antenna_origin=None):
    """
    Place repeated copies of an object along one or more straight lines.

    This function creates a structure group by repeatedly copying an input
    Wireless InSite structure and placing each copy along a selected coordinate
    dimension. The objects are separated by a spacing value returned by the
    ``space`` function. Optionally, antenna vertices can also be generated at a
    fixed offset relative to each placed object.

    Args:
        origin_array: Starting coordinate or list of starting coordinates for
            the placement lines.
        destination_list: Maximum coordinate value for each placement line.
        dim_list: Coordinate dimension used for placement. Use 0 for x, 1 for y,
            or 2 for z.
        space: Callable that returns the spacing between consecutive objects.
        object: Wireless InSite structure object to be copied and placed. It
            must have a valid ``dimensions`` attribute.
        antenna: Optional antenna vertex list template. If provided, antenna
            positions are generated for each placed object.
        antenna_origin: Optional antenna offset relative to each placed object.

    Returns:
        If ``antenna`` is provided, returns a tuple containing the generated
        structure group and antenna vertex list. Otherwise, returns only the
        generated structure group.

    Raises:
        FormatError: If the input object does not have valid dimensions.
    """

    origin_array = np.array(origin_array, ndmin=2)
    n_lines = origin_array.shape[0]
    destination_list = np.array(destination_list, ndmin=1)
    dim_list = np.array(dim_list, ndmin=1)
    # if a list of destination and dim is not provided but a list of origin is,
    # assumes the same destination and dim for all origins
    if len(destination_list) == 1:
        destination_list = np.repeat(destination_list, n_lines)
    if len(dim_list) == 1:
        dim_list = np.repeat(dim_list, n_lines)
    if object.dimensions is None:
        raise errors.FormatError('"{}" has no dimensions'.format(object))

    structure_group = objects.StructureGroup()
    structure_group.name = object.name + ' in line'

    if antenna is not None:
        vertice_list = copy.deepcopy(antenna)
        vertice_list.clear()
        if antenna_origin is None:
            vertice_list_origin = np.array(0, 0, 0)
        else:
            vertice_list_origin = np.array(antenna_origin)

    obj_i = 0

    for origin, destination, dim in zip(origin_array, destination_list, dim_list):
        # position on `dim` accounting for all `object` and `space` placed
        last_obj_loc = origin[dim]
        while True:
            # no more objects fit (last could be the space)
            if last_obj_loc >= destination:
                break
            # check if object fit
            if object.dimensions[dim] + last_obj_loc >= destination:
                break
            # the object to be added
            new_object = copy.deepcopy(object)
            new_object.name += '{:03d}'.format(obj_i)
            # the origin of the new object
            new_object_origin = origin
            new_object_origin[dim] = last_obj_loc
            # move object to the new origin
            new_object.translate(new_object_origin)
            if antenna is not None:
                vertice_list.add_vertice(new_object_origin + vertice_list_origin)
            # add the new object to the structure group
            structure_group.add_structures(new_object)
            # where new objects should be placed
            last_obj_loc = new_object_origin[dim] + new_object.dimensions[dim] + space()
            obj_i += 1
    if antenna is not None:
        return structure_group, vertice_list
    else:
        return structure_group

def rotate(vertice, angle):
    """
    Rotate a 3D vertex counterclockwise around the z-axis.

    The rotation is applied in the x-y plane while preserving the z coordinate.

    Args:
        vertice: Input vertex or coordinate vector ``[x, y, z]``.
        angle: Rotation angle in degrees.

    Returns:
        Rotated vertex as a NumPy array.
    """
    angle = np.radians(angle)

    c = np.cos(angle)
    s = np.sin(angle)
    rot_mat = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    vertice_array = np.matmul(rot_mat, vertice)

    return vertice_array

def get_model(
        c,
        str_vehicles,
        name,
        model_type,
        x,
        y,
        z,
        angle,
        height,
        length=1,
        width=1):
    """
    Load, transform, and append a detailed Wireless InSite object model.

    The model is selected using the SUMO object type instead of its physical
    height. The vertices read from the selected object file are rotated and
    translated to the object's position in the Wireless InSite scenario.

    Args:
        c: Runtime configuration object containing the project working
            directory.
        str_vehicles: Accumulated serialized Wireless InSite geometry.
        name: Name assigned to the generated structure group.
        model_type: SUMO type identifier, such as ``Car``, ``Truck``, ``Bus``,
            ``Pedestrian`` or ``Drone``.
        x: Target x coordinate.
        y: Target y coordinate.
        z: Target z coordinate.
        angle: Rotation angle in degrees.
        height: Physical object height. Retained for compatibility and possible
            future model scaling.
        length: Physical object length. Retained for possible future scaling.
        width: Physical object width. Retained for possible future scaling.

    Returns:
        str: Updated serialized Wireless InSite geometry string.

    Raises:
        ValueError: If the SUMO object type has no configured model or if a
            vertex line is invalid.
        FileNotFoundError: If the selected Wireless InSite model does not exist.
    """

    model_type_normalized = str(model_type).strip().lower()

    model_files = {
        "car": "car.object",
        "truck": "truck.object",
        "bus": "bus.object",
        "pedestrian": "pedestrian.object",
        "drone": "drone.object",
    }

    if model_type_normalized not in model_files:
        raise ValueError(
            "No Wireless InSite model is configured for SUMO type "
            "'{}' used by object '{}'.".format(model_type, name)
        )

    model_path = os.path.join(
        str(c.working_directory),
        "assets",
        "wi_objects",
        model_files[model_type_normalized],
    )

    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            "Wireless InSite model file was not found: {}".format(model_path)
        )

    remaining_vertices = 0

    with open(model_path, "r", encoding="utf-8") as model_object:
        for line_number, line in enumerate(model_object, start=1):

            # Replace the original structure name with the SUMO object ID.
            if "begin_<structure_group>" in line:
                parts = line.split()

                if len(parts) >= 2:
                    parts[1] = str(name)
                    line = " ".join(parts) + "\n"

                str_vehicles += line
                continue

            # Detect the number of vertex lines that follow.
            if "nVertices" in line:
                parts = line.split()

                if len(parts) < 2:
                    raise ValueError(
                        "Invalid nVertices declaration in '{}', line {}: {}"
                        .format(model_path, line_number, line.strip())
                    )

                try:
                    remaining_vertices = int(parts[1])
                except ValueError as exc:
                    raise ValueError(
                        "Invalid vertex count in '{}', line {}: {}"
                        .format(model_path, line_number, parts[1])
                    ) from exc

                str_vehicles += line
                continue

            # Rotate and translate each vertex.
            if remaining_vertices > 0:
                parts = line.split()

                if len(parts) < 3:
                    raise ValueError(
                        "Invalid vertex in '{}', line {}: {}"
                        .format(model_path, line_number, line.strip())
                    )

                try:
                    vertex = np.asarray(
                        [
                            float(parts[0]),
                            float(parts[1]),
                            float(parts[2]),
                        ],
                        dtype=float,
                    )
                except ValueError as exc:
                    raise ValueError(
                        "Non-numeric vertex in '{}', line {}: {}"
                        .format(model_path, line_number, line.strip())
                    ) from exc

                rotated_vertex = np.asarray(
                    rotate(vertex, angle),
                    dtype=float,
                )

                transformed_vertex = [
                    rotated_vertex[0] + float(x),
                    rotated_vertex[1] + float(y),
                    rotated_vertex[2] + float(z),
                ]

                # Preserve any additional fields after x, y and z.
                transformed_parts = [
                    str(transformed_vertex[0]),
                    str(transformed_vertex[1]),
                    str(transformed_vertex[2]),
                ]

                if len(parts) > 3:
                    transformed_parts.extend(parts[3:])

                line = " ".join(transformed_parts) + "\n"
                remaining_vertices -= 1

            str_vehicles += line

    return str_vehicles