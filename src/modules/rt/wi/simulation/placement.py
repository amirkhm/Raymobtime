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
            (x, y), angle, length, width = [f(ped) for f in [
                traci.person.getPosition,
                traci.person.getAngle, #Returns the angle of the named vehicle within the last step [degrees]
                traci.person.getLength,
                traci.person.getWidth
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
                str_vehicles = get_model(c,str_vehicles,ped,xinsite-deltaX,yinsite-deltaY,0,90-angle,1.72) 

    for veh_i, veh in enumerate(traci.vehicle.getIDList()):
        (x, y), (x3,y3,z3), angle, lane_id, length, width, height = [f(veh) for f in [
            traci.vehicle.getPosition,
            traci.vehicle.getPosition3D, #Returns the 3D-position(three doubles) of the named vehicle (center of the front bumper) within the last step [m,m,m]
            traci.vehicle.getAngle,
            traci.vehicle.getLaneID,
            traci.vehicle.getLength,
            traci.vehicle.getWidth,
            traci.vehicle.getHeight
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
        car.translate((x-deltaX, y-deltaY, z3)) #now can translate

        car_structure = objects.Structure(name=veh)
        car_structure.add_sub_structures(car)
        structure_group.add_structures(car_structure)

        if c.vehicles_template:
            str_vehicles = get_model(c, str_vehicles,veh,x-deltaX,y-deltaY,z3,90-angle,height,length,width) 

        #antenna_vertice
        if veh in veh_with_antenna:
            c_present = True
            if ( veh.startswith('dflow') ):
                antenna.add_vertice((x-deltaX, y-deltaY, z3 - 0.1))
            else:
                antenna.add_vertice((x-deltaX, y-deltaY, z3 + height + 0.1))
        if V2V:     
            if veh in Tx_veh:
                c_tx_present = True
                if ( veh.startswith('dflow') ):
                    antenna_Tx.add_vertice((x-deltaX, y-deltaY, z3 - 0.1))
                else:
                    antenna_Tx.add_vertice((x-deltaX, y-deltaY, z3 + height + 0.1))


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

def get_model(c, str_vehicles, name, x, y, z, angle, height, length=1, width=1):
    """
    Load, transform, and append a detailed vehicle model to a serialized object string.

    This function selects a detailed Wireless InSite object model according to
    the object height, reads its vertices, rotates them by the given angle,
    translates them to the target position, and appends the transformed geometry
    to the accumulated vehicle object string.

    The object height is currently used as a classification rule to select the
    model type, such as car, bus, truck, pedestrian, or drone.

    Args:
        c: Runtime configuration object containing the project working directory.
        str_vehicles: Accumulated serialized Wireless InSite vehicle geometry.
        name: Name assigned to the generated structure group.
        x: Target x coordinate.
        y: Target y coordinate.
        z: Target z coordinate.
        angle: Rotation angle in degrees applied to the model vertices.
        height: Object height used to select the corresponding model file.
        length: Optional object length. Currently not used directly. Defaults to 1.
        width: Optional object width. Currently not used directly. Defaults to 1.

    Returns:
        Updated serialized Wireless InSite vehicle geometry string.

    Raises:
        SystemExit: If no detailed model is available for the provided height.
        FileNotFoundError: If the selected model object file does not exist.
        ValueError: If vertex coordinates cannot be converted to numeric values.
    """

    # The height here is utilized as trick to choose which model will be utilized .
    # TODO: Find a new way to classify the models, instead of height.
    if (height == 4.3):
        model_object = open(os.path.join(c.working_directory,'assets/wi_objects/truck.object'), 'r')
    elif (height == 3.2):               
        model_object = open(os.path.join(c.working_directory,'assets/wi_objects/bus.object'), 'r')
    elif (height == 1.59):              
        model_object = open(os.path.join(c.working_directory,'assets/wi_objects/car.object'), 'r')
    elif (height == 1.72):              
        model_object = open(os.path.join(c.working_directory,'assets/wi_objects/pedestrian.object'), 'r')
    elif (height == 0.295): 
        model_object = open(os.path.join(c.working_directory,'assets/wi_objects/drone.object'), 'r')
    else:
        print('There is no model object ready for this object')
        exit(1)

    cn_points = False
    
    for line in model_object:
        if 'begin_<structure_group>' in line:
            tmp = line.split(' ')
            tmp[1] = str(name+ ' ')
            line = ' '.join(tmp)
            str_vehicles += line + "\n"
            continue
        if 'nVertices' in line:
            cn_points = int(line.split(' ')[1]) 
            str_vehicles += line
            continue
        if cn_points:
            tmp = line.split(' ')
            tmp[0] = float(tmp[0])
            tmp[1] = float(tmp[1])
            tmp[2] = float(tmp[2])
            myarray = np.asarray(tmp)
            rotated_v = list(rotate(myarray,angle))
            rotated_v[0] = str(rotated_v[0] + x)
            rotated_v[1] = str(rotated_v[1] + y)
            rotated_v[2] = str(rotated_v[2] + z) + "\n"
            line = ' '.join(rotated_v)
            cn_points -= 1
        str_vehicles += line

    return str_vehicles