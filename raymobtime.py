import argparse

import config as c
from raw_data_handler import todb, gen_csv_coord_file, convert5gmv1ToChannels, gen_beam_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Blensor options
    parser.add_argument('-l', '--lidar', action='store_true',
                        help='Run lidar simulation')
    parser.add_argument('-b', '--base-station', action='store_true',
                        help='Run lidar simulation from the base station perspective')
    parser.add_argument('-p', '--ray-processing', action='store_true',
                        help='Run lidar simulation from the base station perspective')
    parser.add_argument('--beams', action='store_true',
                        help='Run lidar simulation from the base station perspective')
    args = parser.parse_args()
    
    if args.ray_processing:
        todb.gen_database(c)
        gen_csv_coord_file.gen_csv_file(c)
        convert5gmv1ToChannels.gen_rays_dataset(c)
    if args.beams:
        gen_beam_output.gen_beam_output_file(c)