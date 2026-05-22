"""
Raymobtime simulation and post-processing entry point.

This script provides a command-line interface to run the main Raymobtime
workflow stages, including Wireless InSite ray-tracing simulation, Blensor-based
LiDAR/image generation, and post-processing routines for database, coordinate,
ray, beam, LiDAR, and image outputs.

Depending on the selected arguments, it can generate simulation input files,
execute ray tracing, convert raw results into structured datasets, run sanity
checks, or process auxiliary sensor data.
"""
# convert simulation raw to database


if __name__ == "__main__":

    postprocessing_modules = {
        "db": gen_database,
        "coord": gen_csv_file,
        "rays": gen_rays_dataset,
        "beams": gen_beam_output_file,
        "lidar": gen_lidar_matrix,
        "image": image_refinement,
    }

    if args.database == "all":
        for func in [gen_database, gen_csv_file, gen_rays_dataset, gen_beam_output_file]:
            func(c)

    if args.database in postprocessing_modules:
        func = postprocessing_modules[args.database]
        func(c)

    if args.check:
        sanity_check_up(c)

    # Simulation using blensor for image/lidar database
    if (args.blensor):
        blensor_simulation(args.blensor)
        
    # Saving the blensor simulation from pcd files to matrix type data
    CoordSystem = c.CoordSystem
    if args.data_base == "lidar":
        if CoordSystem.lower() == 'spherical':
            gen_lidar_matrix(c)
        elif CoordSystem.lower() == 'cartesian':
            gen_lidar_matrix(c)
        else:
            raise ValueError(f'CoordSystem {CoordSystem} not defined or value incorrect, use cartesian or spherical in config.json')
    elif args.data_base == "image":
        image_refinement(c)

    # Usual Raymobtime Simulation using WI
    if args.place_only or args.ray_tracing_only:
        main(args)