# 🔰 How to Create a Base Scenario

This guide describes the files and resources required to create a Raymobtime base scenario. A base scenario contains the static environment and configuration files used by the mobility, ray-tracing, image, and LiDAR simulation stages.

The document also presents the auxiliary files required during post-processing and explains how detailed object templates can be created for vehicles, pedestrians, drones, and other dynamic objects.

## 1. Base Scenario Overview

A Raymobtime base scenario contains the static files required to reproduce the simulation environment. These files describe the geographic area, road network, mobility configuration, three-dimensional geometry, and wireless propagation scenario.

A typical scenario directory is organized as follows:

```text
📁 data/
└── 📁 <scenario_name>/
    ├── 📁 base/
    │   ├── 🗺️  osm/
    │   │   └── Geographic and map source files
    │   │
    │   ├── 🚦 sumo/
    │   │   └── Network, routes, and mobility configuration
    │   │
    │   ├── 🎥 blender/
    │   │   └── 3D scenario, cameras, and Blensor resources
    │   │
    │   └── 📡 wi/
    │       └── Wireless InSite base project and propagation files
    │
    └── 📁 outputs/sim_x
        └── Simulation results, processed data, images, scans, and channels
```

The exact directory names may vary according to the project configuration, but the base scenario should provide all files required before the simulation starts.

---

# Files Required for Simulation

## 2. OpenStreetMap File

### OSM file (`.osm`)

The OpenStreetMap file contains geographic information about the selected scenario, including roads, intersections, buildings, and other mapped elements.

It may be used to:

* generate the SUMO road network;
* identify road and junction positions;
* support the creation of realistic outdoor scenarios;
* align mobility and three-dimensional environment data;
* provide geographic references for scenario conversion.

The file is usually exported from OpenStreetMap or another compatible geographic data source.

<p align="center">
  <img src="../assets/readme_images/osm.png"
       alt="OSM"
       width="100%">
</p>
<p align="center">
  <em>OpenStreetMap export interface used to select and download the scenario region.</em>
</p>

To export the OSM file, access the [OpenStreetMap website](https://www.openstreetmap.org/), search for the desired geographic region, and adjust the map view so that the complete simulation area is visible. Then, click **Export** in the top menu and select **Manually select a different area** to define the region more precisely. Adjust the selection boundaries to include the roads, intersections, buildings, and surrounding area required by the simulation, and click **Export** to download the file. The downloaded file can then be renamed according to the scenario and stored in the corresponding base directory.

---

## 3. SUMO Files

SUMO is responsible for generating the mobility of vehicles, pedestrians, drones, and other dynamic objects in Raymobtime. A basic SUMO scenario requires three main files: a network file, a route file, and a simulation configuration file.

The files are created in the following order:

<p align="center">
  <img
    src="../assets/readme_images/sumo1.png"
    alt="SUMO file generation workflow"
    width="100%">
</p>

<p align="center">
  <em>Workflow for generating the SUMO network, route, and configuration files from an OpenStreetMap file.</em>
</p>

### 3.1 Network File (`.net.xml`)

The network file contains the road infrastructure used by SUMO. It defines edges, lanes, junctions, connections, traffic directions, speed limits, lane permissions, pedestrian access, and the geometric representation of the roads.

The `.net.xml` file is generated from the OpenStreetMap file exported in the previous section using the SUMO `netconvert` tool. Open a terminal in the directory containing the `.osm` file and execute:

```bash
netconvert --osm-files input_file.osm --numerical-ids.edge-start 0 --numerical-ids.node-start 0 -o output_file.net.xml
```

The command used in the tutorial assigns numerical identifiers to the generated edges and nodes. The option:

```bash
--numerical-ids.edge-start 0
```

configures edge identifiers to start at `0`, while:

```bash
--numerical-ids.node-start 0
```

configures junction or node identifiers to start at `0`.

It is also possible to filter the road types imported from OpenStreetMap. The `--keep-edges.by-type` option keeps only the specified road categories. For example:

```bash
netconvert \
    --osm-files input_file.osm \
    --numerical-ids.edge-start 0 \
    --numerical-ids.node-start 0 \
    --keep-edges.by-type highway.primary,highway.secondary,highway.tertiary,highway.residential \
    -o output_file.net.xml
```

In this example, only primary, secondary, tertiary, and residential roads are preserved in the generated SUMO network.

Alternatively, the `--remove-edges.by-type` option removes selected road categories:

```bash
netconvert \
    --osm-files input_file.osm \
    --numerical-ids.edge-start 0 \
    --numerical-ids.node-start 0 \
    --remove-edges.by-type highway.footway,highway.path,highway.cycleway \
    -o output_file.net.xml
```

The `--keep-edges.by-type` and `--remove-edges.by-type` options should be selected according to the desired scenario. They should not be written together using `/`; the slash shown in the tutorial indicates that either option may be used.

When the scenario includes pedestrians, sidewalks and pedestrian crossings can also be generated:

```bash
netconvert \
    --osm-files input_file.osm \
    --numerical-ids.edge-start 0 \
    --numerical-ids.node-start 0 \
    --osm.sidewalks true \
    --osm.crossings true \
    -o output_file.net.xml
```

The generated network should be inspected before creating the route file. It can be opened in NetEdit using the SUMO graphical interface.

During this inspection, verify that the required roads are present, the directions are correct, the network is connected, and the lanes allow the intended object classes .The edge and lane identifiers required by the route file can be inspected directly in `scenario.net.xml` or through the graphical interface of NetEdit.

> **Note:** The initial network filtering can be performed directly during the OSM conversion by using options such as `--keep-edges.by-type` or `--remove-edges.by-type`. These options are useful for automating the removal of unnecessary road categories at the beginning of the scenario-creation process. However, the generated network can also be opened and manually edited in NetEdit, where unwanted edges, lanes, junctions, and connections can be removed and the resulting `.net.xml` file can be saved. Regardless of the method used, the final network file should contain only the elements required by the simulation, reducing scenario complexity and avoiding invalid or irrelevant mobility routes.

---
### 3.2 Route File (`.rou.xml`)

The route file defines the dynamic objects that move through the SUMO network. It contains the object types, routes, traffic flows, departure intervals, and mobility parameters used during the simulation.

A route file may include conventional vehicles, pedestrians, and drones. Vehicle types describe physical and mobility properties such as length, width, height, acceleration, maximum speed, and behavior parameters. These values are also used by Raymobtime when placing the corresponding objects in Wireless InSite, Blender, and Blensor.

A minimal route file has the following structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>

<routes>

    <!-- Object types and mobility flows are defined here. -->

</routes>
```

#### Vehicle flow

Conventional vehicles may be defined individually or through a type distribution. A distribution allows each generated vehicle to be randomly assigned to one of the configured types.

A vehicle flow specifies the period in which vehicles are generated, the probability of generation, the object type or distribution, and the route followed through the network.

```xml
<flow
    id="flow0"
    begin="10"
    end="100"
    probability="0.41"
    type="typeVehicleDistribution">

    <route edges="E0 E1 E2"/>

</flow>
```

The edges listed in the route must exist in the `.net.xml` file, follow a valid travel direction, and be connected in the specified order.

#### Pedestrian flow

Pedestrians are represented using a type with `vClass="pedestrian"` and a `<personFlow>` element containing a walking stage.

```xml
<vType
    id="Pedestrian"
    vClass="pedestrian"
    speedFactor="1.0"
    length="0.5"
    width="0.5"
    height="1.72"/>
```

```xml
<personFlow
    id="pedFlow0"
    begin="10"
    end="100"
    probability="0.20"
    type="Pedestrian">

    <walk edges="P0 P1"/>

</personFlow>
```

The selected edges must contain lanes that allow pedestrian movement.

#### Drone flow

Drones are represented in SUMO as objects following a predefined horizontal route.

```xml
<vType
    id="Drone"
    length="0.5"
    width="0.5"
    height="0.2"
    accel="2.0"
    decel="2.0"
    maxSpeed="10.0"/>
```

```xml
<flow
    id="droneFlow0"
    begin="10"
    end="100"
    probability="0.10"
    type="Drone">

    <route edges="E0 E1 E2"/>

</flow>
```

SUMO provides the horizontal trajectory of the drone. The `height` attribute defines its physical size and not its flight altitude. Raymobtime applies the configured altitude offset when the drone is placed in the three-dimensional simulation environments.

> **Note:** The identifiers assigned to the object types, such as `Car`, `Truck`, `Bus`, `Pedestrian`, and `Drone`, are used by Raymobtime to select the corresponding detailed object templates. Therefore, these identifiers should remain consistent with the available models and runtime configuration.

#### Automatic route-file generation

Raymobtime currently provides a Python utility that automatically generates a generic `.rou.xml` file. The script writes a predefined vehicle type distribution and creates multiple flows over a configured simulation interval.

Its main parameters are:

| Parameter         | Description                                         |
| ----------------- | --------------------------------------------------- |
| `output_file`     | Path or name of the generated `.rou.xml` file       |
| `initial_time`    | Beginning time of the first generated flow          |
| `end_time`        | Maximum simulation time                             |
| `time_step`       | Interval between the beginning of consecutive flows |
| `flow_duration`   | Intended duration of each flow                      |
| `initial_flow_id` | Initial offset used to generate flow identifiers    |

During execution, the script performs the following operations:

1. creates the XML header and the `<routes>` element;
2. writes the standard vehicle distribution for cars, trucks, and buses;
3. iterates from `initial_time` to `end_time` using `time_step`;
4. assigns a unique identifier to each generated flow;
5. generates a random flow probability;
6. assigns the configured route to each flow;
7. writes the resulting content to the output file.

A simplified usage example is:

```python
generate_generic_route_file(
    output_file="scenario.rou.xml",
    initial_time=5,
    end_time=9000,
    time_step=10,
    flow_duration=5,
)
```
---

### 3.3 SUMO Configuration File (`.sumocfg`)

The SUMO configuration file connects the network and route files and defines the main simulation settings.

Create a file named:

```text
scenario.sumocfg
```

A minimal configuration is:

```xml
<?xml version="1.0" encoding="UTF-8"?>

<configuration>

    <input>
        <net-file value="scenario.net.xml"/>
        <route-files value="scenario.rou.xml"/>
    </input>

    <time>
        <begin value="0"/>
        <end value="100"/>
        <step-length value="0.1"/>
    </time>

</configuration>
```

The file paths are interpreted relative to the directory containing the `.sumocfg` file. If the three files are stored in the same directory, only their filenames are required.


The files should be organized as:

```text
sumo/
├── scenario.net.xml
├── scenario.rou.xml
└── scenario.sumocfg
```

The original OSM file may be kept in the same directory or in a dedicated OSM directory:

```text
base/
├── osm/
│   └── scenario.osm
└── sumo/
    ├── scenario.net.xml
    ├── scenario.rou.xml
    └── scenario.sumocfg
```

---
### 3.4 Validating the SUMO Scenario

After creating the network, route, and configuration files, the complete mobility scenario should be validated using the SUMO graphical interface. Open SUMO GUI, select **File → Open Simulation**, and load the corresponding `.sumocfg` file. Once the configuration is loaded, click the **Run** button to start the simulation and observe the movement of the configured vehicles, pedestrians, and drones throughout the road network.

<p align="center">
  <img src="../assets/readme_images/sumo2.png"
       alt="Opening and running a SUMO simulation"
       width="100%">
</p>

<p align="center">
  <em>Opening the SUMO configuration file and running the mobility simulation in SUMO GUI.</em>
</p>

During validation, confirm that the road network is displayed correctly and that the dynamic objects enter and move through the scenario according to the expected routes and simulation times. The visualization should also be used to identify disconnected edges, invalid routes, incorrect lane permissions, unexpected vehicle behavior, or objects leaving the intended simulation area.

Before using the scenario in Raymobtime, verify that:

* the network and configuration files load without errors;
* every route references valid edges from the `.net.xml` file;
* consecutive edges are connected and follow a valid travel direction;
* vehicle lanes permit the configured vehicle classes;
* pedestrian routes use lanes that allow pedestrian movement;
* the simulation start time, end time, and time step are correct;
* vehicles, pedestrians, and drones enter the network as expected;
* objects do not become teleported because of disconnected or congested routes;
* the traffic density and flow probabilities are appropriate for the scenario;
* the selected mobility area is spatially consistent with the Wireless InSite and Blender environments.

The final `.net.xml` file should contain only the roads, lanes, junctions, and connections required by the intended mobility simulation. Unnecessary elements may increase scenario complexity and make route validation more difficult.

Once the SUMO scenario runs correctly, the resulting files can be used as the mobility base from which Raymobtime generates the sequence of scenes and episodes.

---

## 4. Blender Scenario

### Blender file (`.blend`)

The Blender file contains the three-dimensional visual representation of the scenario.

It may include:

* buildings;
* roads;
* sidewalks;
* vegetation;
* street furniture;
* cameras;
* lighting;
* static environmental objects;
* reference points used for coordinate alignment.

Raymobtime uses the Blender scenario for RGB image rendering and as the geometric environment used by Blensor during LiDAR generation.

Example:

```text
scenario.blend
```

The Blender scenario must be spatially aligned with the SUMO and Wireless InSite environments. Coordinate differences among the simulators must be handled during scenario preparation or runtime placement.

The file should also contain the cameras required by the selected simulation mode. For example, base-station image generation may require objects named:

```text
Camera0
Camera1
Camera2
```

The number of available cameras must be compatible with the value defined in the Raymobtime configuration.

---



## 5. Wireless InSite Base Scenario

The Wireless InSite base scenario contains the static geometry and propagation configuration used during electromagnetic ray tracing.

It may include:

* buildings;
* ground materials;
* roads;
* vegetation;
* static structures;
* waveform definitions;
* antenna definitions;
* propagation models;
* study areas;
* base-station positions;
* receiver grids;
* ray-tracing parameters.

The base scenario must be prepared before Raymobtime starts repositioning the mobile objects.

Typical Wireless InSite resources may include:

```text
scenario.setup
scenario.studyarea
scenario.txrx
scenario.object
scenario.material
```

The exact files depend on the Wireless InSite project version and scenario configuration.

Raymobtime uses the base scenario to generate run-specific simulations in which vehicles, pedestrians, drones, transmitters, and receivers are inserted or repositioned.

The Wireless InSite coordinate system must be aligned with the SUMO and Blender coordinate systems.

---

# Files Required for Post-processing

## 6. Antenna Codebook

The antenna codebook contains the beamforming vectors or antenna configurations used during wireless channel generation and processing.

Example:

```text
default_mikrotik_cb.npy
```

A codebook may define:

* beam identifiers;
* antenna weights;
* phase shifts;
* beam directions;
* transmitter beams;
* receiver beams.

The selected codebook must be compatible with the antenna array and channel representation used by the scenario.

Codebooks are typically stored in:

```text
assets/codebooks/
```

Example:

```text
assets/codebooks/default_mikrotik_cb.npy
```

---

## 7. H-matrix Configuration or Data

The H-matrix represents the wireless channel between transmitter and receiver antenna elements.

Depending on the Raymobtime workflow, it may be generated from:

* Wireless InSite propagation paths;
* angles of departure and arrival;
* propagation delays;
* path powers;
* antenna array geometry;
* codebook information.

The H-matrix may be stored in formats such as:

```text
.npy
.npz
.h5
.mat
```

The required input files and output format depend on the selected channel-generation module.

The scenario documentation should specify:

* the antenna dimensions;
* the transmitter and receiver array configuration;
* the carrier frequency;
* the number of paths;
* the expected H-matrix dimensions;
* the codebook used during beam processing.

---

## 8. Camera Calibration Information

When RGB images are enabled, post-processing may require camera information exported from the Blender scenario.

The camera metadata may include:

* camera position;
* camera rotation;
* focal length;
* sensor width;
* sensor height;
* image resolution;
* clipping distances.

Example output:

```text
processed_data/
└── blend_info/
    └── cam_info.json
```

These values are used to generate the camera intrinsic matrix and associate image pixels with the three-dimensional environment.

---

## 9. LiDAR Point Clouds

When LiDAR generation is enabled, Blensor produces point-cloud files associated with the selected transmitters or receivers.

Common formats include:

```text
.pcd
.zip
.npy
```

The post-processing stage may:

* translate the point cloud to the local sensor reference system;
* remove invalid points;
* convert Cartesian coordinates to spherical coordinates;
* generate spherical LiDAR matrices;
* associate scans with scenes, episodes, transmitters, and receivers.

Temporary scan files should be generated inside the configured LiDAR output directory and removed after compression or conversion.

---

# Extra: Creating an Object Template

## 10. Detailed Object Templates

Raymobtime can represent dynamic objects using simplified rectangular prisms or detailed object templates.

Detailed templates may be created for:

* cars;
* buses;
* trucks;
* pedestrians;
* drones;
* motorcycles;
* bicycles;
* custom mobile objects.

Wireless InSite object templates are typically stored in:

```text
assets/wi_objects/
```

Example:

```text
assets/wi_objects/
├── car.object
├── bus.object
├── truck.object
├── pedestrian.object
└── drone.object
```

The object template should contain the geometry expected by the Wireless InSite object parser.

During placement, Raymobtime:

1. selects the template according to the SUMO object type;
2. reads the template vertices;
3. rotates the vertices according to the SUMO orientation;
4. translates the model to the scenario coordinates;
5. assigns the SUMO object identifier to the generated structure.

Model selection should be based on the SUMO type identifier rather than on the physical object height.

For example:

```python
model_files = {
    "car": "car.object",
    "truck": "truck.object",
    "bus": "bus.object",
    "pedestrian": "pedestrian.object",
    "drone": "drone.object",
}
```

This approach allows the object dimensions to be changed in the SUMO route file without requiring modifications to the Raymobtime source code.

---

## 11. Base Scenario Validation

Before running a complete dataset simulation, verify that:

* the SUMO network loads without errors;
* all route edges exist in the network;
* pedestrian lanes allow pedestrian traffic;
* the Blender scenario opens correctly;
* the required cameras exist;
* the Wireless InSite base project opens correctly;
* the scenario coordinate systems are aligned;
* the selected object templates exist;
* the codebook path is valid;
* the output directories can be created;
* the required post-processing files are available.

A minimal test should be executed before generating a large number of episodes and scenes.

---

# Scenario Structure

A scenario is composed of the following elements:

```text
data/rosslyn
├── base
│   ├── blender
│   │   ├── rosslyn-2_29b.blend
│   │   ├── rosslyn-4_5_4-1c0.blend
│   │   ├── rosslyn-4_5_4-1c.blend
│   │   └── vehicles.blend
│   ├── config.json
│   ├── Descricao
│   ├── sumo
│   │   ├── seasonal.net.xml
│   │   ├── seasonal.rou.xml
│   │   └── seasonal.sumocfg
│   └── wi
│       ├── base.object
│       ├── base.study.xml
│       ├── base.txrx
│       ├── model.setup
│       ├── model.study.diag
│       ├── model.study.xml
│       ├── model.txrx
│       ├── model.vw
│       ├── model.X3DGeometryAllEdges.cache
│       ├── model.X3DGeometryAllEdges.diag
│       ├── model.X3DGeometryAllEdges.xml
│       ├── random-line.object
│       ├── Rosslyn.city
│       ├── Rosslyn_DTED.ter
│       ├── study
│       └── X3DGeometryAllEdges
└── out
    └── sim_a
        ├── config.yaml
        ├── postprocessed
        ├── processed_data
        └── rt_simulations
```

Describe each directory according to the project organization.