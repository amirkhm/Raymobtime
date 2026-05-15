# Usage

Change the config.json file:

```
"blensor_options":{
    "path_to_scenario":"/mnt/data/Scenarios/Rosslyn/rosslyn.blend",
    "blensor_img_path":"Blensor"
}
```

**path_to_scenario** being the path to the blender scenario, **blensor_img_path** being the path to the Blensor image app.

Other variables that you'll need to modify:

- **results_dir_path**: path to the raymobtime simulation (the runs)
- **n_init_run**: initial run
- **n_end_run**: final run

if you're running image simulation, you'll need to include the coordinate file such as **CoordVehiclesRxPerScene_s009.csv**

After that, run

`python3 blensor/blensor_src.py -l`

for lidar simulation

`python3 blensor/blensor_src.py -i`

for image simulation

