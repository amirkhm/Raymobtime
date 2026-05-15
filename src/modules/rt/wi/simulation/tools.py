import numpy as np
import traci

def pick_car_from_area(veh_list, area_lim, n_veh, return_counts=False):
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
