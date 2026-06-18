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

The `.net.xml` file can be generated from the OSM file exported in the previous section. Open a terminal in the directory containing the OSM file and execute:

```bash
netconvert \
    --osm-files scenario.osm \
    --output-file scenario.net.xml
```

The same command can be written in a single line:

```bash
netconvert --osm-files scenario.osm -o scenario.net.xml
```

After the command finishes, the directory should contain:

```text
scenario.osm
scenario.net.xml
```

When the scenario includes pedestrians, sidewalks and crossings can also be imported from OpenStreetMap:

```bash
netconvert \
    --osm-files scenario.osm \
    --osm.sidewalks true \
    --osm.crossings true \
    --output-file scenario.net.xml
```

The generated network should be inspected before creating the routes. It can be opened with:

```bash
netedit scenario.net.xml
```

or:

```bash
sumo-gui -n scenario.net.xml
```

During this inspection, verify that the required roads are present, the directions are correct, the network is connected, and the lanes allow the intended object classes.

A network edge may be represented as:

```xml
<edge id="E0" from="J0" to="J1">
    <lane
        id="E0_0"
        index="0"
        speed="13.89"
        length="100.0"/>
</edge>
```

In this example, `E0` is the edge identifier, while `J0` and `J1` are junction identifiers. Routes must reference edge identifiers and not junction identifiers.

Therefore, the correct route is:

```xml
<route edges="E0"/>
```

The following route is invalid because `J0` and `J1` are junctions:

```xml
<route edges="J0 J1"/>
```

For pedestrian-only lanes, the network may contain:

```xml
<lane
    id="E0_0"
    index="0"
    allow="pedestrian"
    speed="2.0"
    length="100.0"/>
```

The edge and lane identifiers required by the route file can be inspected directly in `scenario.net.xml` or through the graphical interface of NetEdit.

---

### 3.2 Route File (`.rou.xml`)

The route file defines the dynamic objects that move through the SUMO network. It contains vehicle types, vehicle distributions, pedestrian types, routes, traffic flows, departure times, speeds, and movement probabilities.

Create a file named:

```text
scenario.rou.xml
```

A minimal route file has the following structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>

<routes>

    <!-- Object types and mobility flows are defined here. -->

</routes>
```

#### Vehicle types

Vehicle types describe the physical dimensions and mobility properties of each object class:

```xml
<vTypeDistribution id="typeVehicleDistribution">

    <vType
        id="Car"
        accel="3.0"
        decel="4.5"
        length="4.645"
        width="1.775"
        height="1.59"
        maxSpeed="17.88"
        speedDev="0.1"
        sigma="0.2"
        minGap="0.3"
        probability="0.2"/>

    <vType
        id="Truck"
        accel="2.0"
        decel="4.0"
        length="12.5"
        width="2.5"
        height="4.3"
        maxSpeed="17.88"
        speedDev="0.1"
        sigma="0.2"
        minGap="0.3"
        probability="0.5"/>

    <vType
        id="Bus"
        accel="2.0"
        decel="4.0"
        length="9.0"
        width="2.4"
        height="3.2"
        maxSpeed="17.88"
        speedDev="0.1"
        sigma="0.2"
        minGap="0.3"
        probability="0.3"/>

</vTypeDistribution>
```

The probabilities inside a distribution should represent the desired proportion of each vehicle type.

#### Vehicle flows

A vehicle flow defines when objects enter the simulation and which edges they follow:

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

The edges must exist in `scenario.net.xml`, appear in a valid travel direction, and form a connected route.

#### Pedestrian flows

A pedestrian type must use the `pedestrian` vehicle class:

```xml
<vType
    id="Pedestrian"
    vClass="pedestrian"
    speedFactor="1.0"
    speedDev="0.1"
    length="0.5"
    width="0.5"
    height="1.72"/>
```

Pedestrian mobility is defined with `<personFlow>` and `<walk>`:

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

The selected edges must contain lanes that allow pedestrians.

#### Drone flows

A drone can be represented in SUMO as a vehicle type that follows a predefined horizontal route:

```xml
<vType
    id="Drone"
    accel="2.0"
    decel="2.0"
    length="0.5"
    width="0.5"
    height="0.2"
    maxSpeed="10.0"
    speedDev="0.1"
    sigma="0.1"
    minGap="0.1"/>
```

The drone flow can then be defined as:

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

SUMO provides the horizontal movement of the drone. The `height` attribute represents the physical size of the drone and not its flight altitude. Raymobtime applies the configured vertical offset when placing the drone in Wireless InSite, Blender, and Blensor.

A complete route file may therefore contain vehicle, pedestrian, and drone flows:

```xml
<?xml version="1.0" encoding="UTF-8"?>

<routes>

    <vTypeDistribution id="typeVehicleDistribution">
        <vType
            id="Car"
            accel="3.0"
            decel="4.5"
            length="4.645"
            width="1.775"
            height="1.59"
            maxSpeed="17.88"
            probability="1.0"/>
    </vTypeDistribution>

    <vType
        id="Pedestrian"
        vClass="pedestrian"
        speedFactor="1.0"
        length="0.5"
        width="0.5"
        height="1.72"/>

    <vType
        id="Drone"
        accel="2.0"
        decel="2.0"
        length="0.5"
        width="0.5"
        height="0.2"
        maxSpeed="10.0"/>

    <flow
        id="flow0"
        begin="10"
        end="100"
        probability="0.41"
        type="typeVehicleDistribution">
        <route edges="E0 E1 E2"/>
    </flow>

    <personFlow
        id="pedFlow0"
        begin="10"
        end="100"
        probability="0.20"
        type="Pedestrian">
        <walk edges="P0 P1"/>
    </personFlow>

    <flow
        id="droneFlow0"
        begin="10"
        end="100"
        probability="0.10"
        type="Drone">
        <route edges="E0 E1 E2"/>
    </flow>

</routes>
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

</configuration>
```

The file paths are interpreted relative to the directory containing the `.sumocfg` file. If the three files are stored in the same directory, only their filenames are required.

Simulation time settings can also be included:

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

After creating the three files, open the complete simulation with:

```bash
sumo-gui -c scenario.sumocfg
```

The graphical interface should load the road network and display the configured objects when the simulation starts.

Before using the files in Raymobtime, verify that:

* the network loads without errors;
* every route references valid edges;
* consecutive route edges are connected;
* vehicle lanes permit the configured vehicle classes;
* pedestrian routes use pedestrian-accessible lanes;
* the simulation start and end times are correct;
* vehicles, pedestrians, and drones enter the scenario as expected;
* no object becomes teleported because of an invalid route;
* the selected mobility region corresponds to the Wireless InSite and Blender environments.

The resulting SUMO files provide the mobility base used by Raymobtime to generate the sequence of scenes and episodes.

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



## Tutorial geração de dataset para machine learning com Raymobtime

Instalar SUMO e Wireless Insite

Clonar repositórios: 
- [gitlab raymobtime](https://gitlab.lasse.ufpa.br/software/raymobtime-project/raymobtime/-/tree/master?ref_type=heads).

Recomendação de organização de arquivos:
- Na pasta base files de raymobtime, crie uma pasta com o nome do seu cenário
- Dentro dessa pasta crie as pastas: sumo, meshes, wi
- Em sumo serão guardados os arquivos sumo
- Em meshes serão guardados os arquivos 3d exportados do blender para importação no wireless insite
- Em wi será guardado o projeto do wireless insite

### 1. Open street map

1. Abrir site [Open street map](https://www.openstreetmap.org).
1. Ir para a área de interesse, é possivel editar em edit.
1. Ir em export, selecionar area manualmente, selecionar a área, clicar em Exportar. Será gerado um arquivo .OSM
- Obs: Guardar .OSM na pasta do cenário.

### 2. Conversão .OSM --> .NET.XML
Converter o arquivo .OSM para o formato .NET.XML, que descreve os elementos de tráfego.. No terminal utilize o comando a seguir, realizando os ajustes indicados.
- Ajuste o inputFile para o nome do seu arquivo .osm, e o nome do outputFile.
- Deixar ou o keep ou o remove. Se der erro em algum highway, remover o highway problemático. (é possivel retirar o os keeps e highways, ficam todas as ruas)
```bash
netconvert --osm-files inputFile.osm --numerical-ids.edge-start 0 --numerical-ids.node-start 0 --keep-edges.by-type/--remove-edges.by-type highway.secondary, highway.residente -o outputFile.net.xml
```
- Guardar na pasta sumo
- Abrir .NET.XML e ajustar netOffset="X,Y" e projParameter="!". As coordenadas para o netOffset serão obtidas ao fazer placement no raymobtime, não alterar por enquanto.

### 3. Sumo
Instalar sumo normalmente.
1. Abrir o NET.XML no SUMO e ver se está ok as edges, criar caso nescessário
1. Pegar o Id das ruas da rota e ajustar no rustic.py
1. Rodar o rustic.py, irá gerar o .rou.xml
1. Ajustar o .sumo.cfg manualmente (a parte dos arquivos)
1. Conferir o .sumo.cfg como network, analizar o flow
1. Guardar na pasta sumo

### 4. Blender
[blender versão 2.79](https://www.blender.org/download/releases/2-79/)

[Blosm extension](https://github.com/vvoovv/blosm)

[Bash export](https://github.com/mrtripie/Blender-Super-Batch-Export)

1. Importar o .OSM via blosm
    - Option: file, marcar buildings e roads and paths.
1. Excluir elementos desnecessários, ajustar como meshes, criar plano ground, salvar como .blend
1. Exportar meshes como .dae via bash export, guardar na pasta meshes

### 5. Wireless insite
Instalar versão 3.3
1. Colocar o random-line.object e base.object na pasta meshes
1. Para passar de um sistema operacional para outro usar no terminal na pasta meshes
    ```bash
    find . -type f -print0 | xargs -0 -n 1 -P 4 unix2dos
    ```
1. Copiar os arquivos para o windows para a pasta de wi
1. Abrir o WI em geometry: open random.line como object (ele deve aparecer, é um bolco de metal) e import meshes no WI como city.
1. Ajustar materiais, onda (sinusoid), criar antenas, transmissores (nome: Tx)(atrentar para suas posições) e receptores (nome: Rx) em  transceivers (atribuir atenas), área de estudo (nomear como study)(X3D). 

    #### configurações da study area
    - Short description como study.
    - Modelo de propagação X3D.
    - Setar número de raios por par Tx Rx.
    - outputs: (1) propagation paths, (2) received power, (3) complex E-fields, (4) complex impulse response, (5) delay spread.

1. Clicar no botão de run para averiguar os raios
1. Conferir os raios gerados
1. Salvar projeto com o nome model
1. Copiar os arquivos model.txrx como base.txrx e o model.study.xml como base.study.xml
1. Analise onde é o 0, 0 x e y no wireless, abra seu .net.xml e verifique a coordenada do mesmo ponto, ajuste no seu .net.xml na parte netoffset (x,y). Para verificar se está ok precisa rodar o placement no raymobtime.

### 6. Raymobtime
1. Ajustar config.json
1. Rodar placement
    ```bash
    python3 simulation -po
    ```

1. Abrir algumas run gerada, verificar se as posições dos veiculos batem com ajuste de coordenadas.

1. Se tudo estiver ok, rodar traçado de raios 
    ```bash
    python3 simulation -rj
    ```

1. Verificar o traçado de algumas das runs

1. Rodar db, coord, rays, beams, images...

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