base_config:     
  output_name: "sim_a"                        
  % Description: Simulation identifier name
  % Status: working

  scenario: "rosslyn"                      
  % Description: scenario name
  % Status: working
  resume: true                                
  Description: skip steps already concluded (not implemented, necessary logging of concluded steps)
  % status
  clean_previous: true                       
  % Description: remove result folders before running
  % Status: working

pipeline:
  mobility:
    enabled: true 
    % Status: working
    tool: "sumo"                              # null | none
    placement_limits: 
      enabled: false
      max_lim: [843, 523]                     # [x, y] study area limits for placement of Tx and Rx
      min_lim: [660, 334]                     # [x, y] study area limits for placement of Tx and Rx
      ##end_ep_for_no_veh: true #nop
  
  ray_tracing:                                # parsing automático
    enabled: true 
    % Status: working
    #tool: "wireless_insite"                  # wireless_insite | none
    jump: true   
  
  blensor:
    enabled: false 
    outputs: 
      - "lidar"
      - "image"

  post_processing:
    enabled: false  
    which: "all"                              # all | selected
    outputs:                                  # ["db", "coord", "rays", "beams", "image", "lidar"]
      - "db"                                  # database (sqlite/postgres/hdf5)
      - "coord"                               # coordenadas
      - "rays"
      - "beams"
      - "image"
      - "lidar"
  
  validation:
    run_checkup: false  

rmt:
  enabled: true                               # false for isolated simulation
  % Status: working
  scenes_per_episode: 2 
  % Status: working
  time_between_episodes: 35                   # This time needs to be multiple of scene time step
  % Status: working
  sampling_parameters: [0, 6, 0.5]          # start, end, step
  % Status: working
  features:
    fixed_receivers: false  
    vehicles_template: true 
    % Status: working

sumo:
  seed: 10  
  % Status: working
  bin: /usr/bin/sumo 
  % Status: working
  cfg: seasonal 
  % Status: working

ray_tracing:
  use_pedestrians: false
  use_drone: false
  receivers_per_episode: 1
  % Status: working
  transmitters_per_episode: 1
  % Status: working
  v2v:
    enabled: false
    close_vehicles: true
    n_of_vehicles: 7
    chose_vehicle: false
    chosen_vehicle: Truck
  wireless_insite:
    software_path: /home/gabriel/softwares/wireless-insite/remcom
    % Status: working
    LICENSE_FILE: REMCOMINC_LICENSE_FILE=2501@10.10.80.6
    % Status: working
    base_files_names:
      study_area_name: study
      % Status: working
      tx_name: Tx
      % Status: working
      rx_name: Rx
      % Status: working
      setup_name: model
      % Status: working
      vehicles_name: random-line
      % Status: working
  
blensor_options:
  path_to_scenario_blend: /home/gabrielferreiravieira/Documents/repositories/r2/raymobtime/base_files/B-pnm-SP/Blender/B-pnm-SP.blend
  path_to_vehicles_blend: /home/gabrielferreiravieira/Documents/repositories/r2/raymobtime/base_files/B-pnm-SP/Blender/vehicles.blend
  path_blensor_image: ~/Blensor-x64.AppImage
  image_options:
    BS_camera: false
    UE_camera: false
    n_camera_BS: 3

post_processing:
  area_of_analyses: # only fill hdf5 with objects within this area
    enabled: false
    limits: [660, 334, 843, 523]              #[x1,y1, x2, y2]

  mimo:
    import_precoding: Codebook/default_mikrotik_cb.npy
    import_channels: true
    import_combining: false
    antenna_array_expansion:
      Tx: [6, 6] #[x, y]
      Rx: [1, 1] #[x, y]
      normalized_antenna_distance: 0.5
    array_rotation:
      Tx: [0,0,0] #[alpha, beta, gamma]
      Rx: [0,0,0] #[alpha, beta, gamma]
    
  cartesian_lidar_matrix:
    coordinate_system: cartesian  #[spherical | cartesian]
    QP: # cartesian
      step: [1.15, 1.25, 1]  # step in x, y, z directions
      min: [744, 429, 0]      # minimum x, y, z coordinates
      max: [767, 679, 10]     # maximum x, y, z coordinates
    QPsph:
      step: [1.15, 1.25, 1]         # step in r, theta, phi directions
      min: [744, 429, 0]
      max: [767, 679, 10]
    Tx_position: [13.735024754781474, 12.543859564388237, 25.0] #[x,y,z]
    max_dist_LIDAR: 100
    type_data: 3D # 2D | 3D