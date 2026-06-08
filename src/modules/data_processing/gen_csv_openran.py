import os

def main():
    """
    Generate a receiver coordinate CSV file from SUMO output files.

    This function iterates over a fixed number of Raymobtime simulation runs,
    reads the corresponding SUMO output file for each run, extracts receiver
    vehicle information, and writes the selected fields to a consolidated CSV
    file named ``CoordVehicleTxRx.csv``.

    The generated CSV contains one row per valid vehicle entry and includes
    episode ID, scene ID, receiver ID, vehicle name, vehicle type, position,
    and orientation angle.

    Returns:
        None. The extracted data is written directly to the output CSV file.

    Raises:
        FileNotFoundError: If one of the expected SUMO output files does not
            exist.
        IndexError: If a SUMO output row does not contain the expected number
            of comma-separated fields.
    """
    SIMULATION = "simulations/s004"
    RUNS = 2000
    FILE_NAME = 'CoordVehicleTxRx.csv'

    csv_file = open(FILE_NAME, 'w')
    csv_file.writelines('Val,EpisodeID,SceneID,RxID,VehicleName,TypeID,x,y,z,angle\n')

    sumo_file_name = "sumoOutputInfoFileName.txt"
    for run in range(RUNS):
        sumo_file = os.path.join(SIMULATION, f'run{run:05d}',sumo_file_name)
        with open(sumo_file) as f:
            reader = f.read()
            for row in reader.split('\n'):
                if '"' in row or len(row)<1:
                    continue
                info = row.split(',')
                episode = info[0]
                scene = info[1]
                rx = info[2]
                veh = info[3]
                type_id = info[5]
                x = info[6]
                y = info[7]
                z = info[16]
                angle = info[12]
                line = ','.join(['V', episode, scene, rx, veh, type_id, x, y, z, angle])
                csv_file.writelines(line)
                csv_file.writelines('\n')

if __name__ == "__main__":
    main()
