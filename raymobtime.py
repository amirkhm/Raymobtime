import argparse

import config as c
# convert simulation raw to database
from raw_data_handler import gen_database, gen_csv_file, gen_rays_dataset, gen_beam_output_file
from raw_data_handler import gen_lidar_matrix
# simulators
from blensor import blensor_simulation
from rwisimulation.simulation import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Blensor options    
    parser.add_argument('-d', '--data-base', choices=["db", "coord", "rays", "beams", "lidar", "all"], const="all", nargs="?",
                        help='Convert simulation from WI to database type: db, csv, hdf5')
    parser.add_argument('-b', '--blensor', choices=["lidar", "image"],
                        help='Uses Blensor to simulate lidar and image data for Raymobtime dataset')
    # Old args for simulation from rwisimulation
    parser.add_argument('-p', '--place-only', action='store_true',
                        help='Run only the objects placement and save files for ray-tracing')
    parser.add_argument('-j', '--jump', action='store_true',
                        help='Jumping runs that already have results (works only if utilized with the option \'-r\' )')
    parser.add_argument('-r', '--ray-tracing-only', action='store_true',
                        help='Run only ray-tracing with previoulsy generated files')
    parser.add_argument('-c', '--run-calcprop', action='store_true',
                        help='Ray-tracing with InSite calcprop instead of the default wibatch')
    parser.add_argument('-s', '--pause-each-run', action='store_true',
                        help='Interactive run')
    parser.add_argument('-o', '--remove-results-dir', action='store_true',
                        help='ONLY IF YOU KNOW WHAT YOU ARE DOING: it will remove the whole results folder')
    parser.add_argument('-m', '--mimo-only', action='store_true',
                        help='Run only ray-tracing with native mimo from InSite previoulsy generated files')
    args = parser.parse_args()
    
    # Saving the simulation files into database type db, csv, hdf5
    # and generating beams
    if args.data_base == "all":
        gen_database(c)
        gen_csv_file(c)
        gen_rays_dataset(c)
        gen_beam_output_file(c)
    else:
        if args.data_base == "db":
            gen_database(c)
        if args.data_base == "coord":
            gen_csv_file(c)
        if args.data_base == "rays":
            gen_rays_dataset(c)
        if args.data_base == "beams":
            gen_beam_output_file(c)

    # Simulation using blensor for image/lidar database
    if (args.blensor):
        blensor_simulation(args.blensor)
        
    # Saving the blensor simulation from pcd files to matrix type data
    if args.data_base == "lidar":
        gen_lidar_matrix(c)
    
    # Usual Raymobtime Simulation using WI
    if args.place_only or args.ray_tracing_only:
        main(args)