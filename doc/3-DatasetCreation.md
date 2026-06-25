# Overview

This document is a tutorial guide on how generating datasets using raymobtime.

## General base concept 
The core idea of generated datasets is simulate a scenario where communication happens.

For that it is necessary define where it happens, that is a 3D scenario, how is the environment state, who are the communication elements and where they are positioned. 

The mobility simulator is responsible por inform where mobile objects are placed and respective orientation and speed.

The raytracing simulator is responsible for characterizing radio  communication elements and the environment, in order to simulate propagation characteristics of eletromagnetic fields at the communication scenario.

The 3D computer graphics software is responsible for rendering images taken from positions of interest at referred 3D environment and also simulate a lidar sensor. The positions of interest tend to be the receiver or transmitter positions.

>Note that some in some moments User Equipament (UE) and Base Station (BS) are used to refer to receiver and transmitter elements, respectively. 

All This context that refers to where, how and who communicates in a given situation is here referred to a base.

If in your kind of interest, [how create a base](/doc/2-BaseCreation.md) is a doc that gives a tutorial on how creating your own base, with your desired circunstances.

## What expect from dataset

Since you already have a base where you plan communication happen, you may question yourself: 

> 🤔 What kind of outputs am i generating with raymobtime?

Following the [methodology](/README.md) described, time sampples of the communication system are taken. At each sample is known the state of elements of interest, as described below:

* Cartesian coordinates of mobile objects
* Cartesian coordinates of transmitter and receiver elements
* Ray-tracing outputs
    * Propagation paths.
    * Received power.
    * Complex E-fields.
    * Complex impulse response.
    * Delay spread.
* Images of referred time instant from UE and BS points of view.
* Lidar point clouds obtained at receivers position
* Post processed rt outputs
    * Multiple Input Multiple Output (MIMO) communication system using geometric channel approach.
* Post processed image outputs
    * Images from transmitter point of view with bounding boxes at receivers.
* Post processed lidar outputs
    * Voxelized 2D/3D lidar matrixes using cartesian/spherical coordinates using receiver as reference point.

The use of this data may vary depending on your focus, but it is commonly used for machine learning in beam selection or beam tracking problems.

# How generate desired outputs

Considering you already have a base, all necessary configurations are done at [YAML](/config.yaml) of configuration. This section describes how configure the [YAML](/config.yaml) and what are the implemented features.

The structure the file follows as below

    base_config: (...)
    pipeline: (...)
    rmt: (...)
    sumo: (...)
    ray-tracing: (...)
    blensor_options: (...)
    data_processing: (...)
    post_processing: (...)

## Configuring __base_config__

First, you need to refer to your respective base, so configure base_config entries.

* __scenario__: < ```string``` >
    * Base name at [data](/data/) folder

* __output_name__: < ```string``` >
    * Sets a name for your simulation, this is very useful when you have to configure many variations of outputs using the same base.

* __yaml_output__: < ```boolean``` >
    * Save the a copy of [YAML](/config.yaml) at the output folder, in order to document the configuration used to achieve that outputs.

* __logging_level__: < ```option``` >
    * Sets the logging level, in order to follow the status of simulation in real time. 

    __Options__: ```debug```, ```info```, ```warning```, ```error```, ```critical```, ```NONE```

* __resume__: < ```boolean``` >
    * Skip steps already concluded, if false remember to clean previous outputs.

* __clean_previous__: < ```list``` of options , empty ```list``` >
    * Clean listed outputs in order to re-run and the results. It turns to be important when something in pipeline changes.
    * __Options for list__: ```mobility```, ```rt```, ```db```, ```coord```, ```hdf5```, ```blensor_lidar```, ```blensor_images```, ```post_lidar```, ```post_images```, ```beams```.

## Configuring pipeline

The way raymobtime was constructed there is an actual pipeline followed, where an order of events happen. The logic will be here explicited.

### mobility

In case of existence of mobile objects, a mobility tool is needed to inform where the objects are placed at a referred instant also the orientations and speed.

The objects position obtaining at a given instant here is called placement. Given the interest of communication channel elements, they may or not be attached to mobile objects. This context refers to the difference of an antenna with fixed position or fixed to a mobile structure, that carry and consequently changes the antenna position according to object designed movement.

> Parameters

* __enabled__: < ```boolean``` >
    * Enable/disable mobility;

* __tool__: < ```option``` > 
    * Select the mobility tool used;

        __Options__: ```sumo```.

    Obs: Currently, there is only one tool implemented for manage mobility, the Simulator of Urban Mobility (SUMO).
    
* __placement_limits__:
    
    Select a rectangular area from where choose mobile objects to carry antennas at the beginning of an episode. Compatible with SUMO.

    > Parameters

    * __enabled__: < ```boolean``` >
        * Enable/disable select a specific area of choose;  

    * __max_lim__: < ```[x_float, y_float]``` >
        * Right superior coordinate of the rectangular area of interest;

    * __min_lim__: < ```[x_float, y_float]``` >
        * Left inferior coordinate of the rectangular area of interest;

### ray_tracing

Used for calculate multipath components, in order to simulate communication channels with spatial consistency. 

> Parameters

* __enabled__: < ```boolean``` >
    * Enable/disable ray-tracing of runs

* __tool__: < ```option``` >
    * Select the ray-tracing tool used;
    
        __Options__: WirelessInsite

        Obs: Currently, there is only one tool implemented for implement ray-tracing, Wireless Insite.

* __jump__: < ```boolean``` >
    * Check ray-tracing running status from runs, it continues from last run not completed, skips already completed. 

### data_processing

Generate data structures to centralize data. This structures are a sql database containg objects and rays information, a csv with coordinates information and hdf5 file with rays information for each episode.

> Parameters

* __enabled__: < ```boolean``` >
    * Enable/disable data structures generating.

* __which__: < ```option``` >
    * Choose which structures generate. Select ```all``` for generating sql, csv and hdf5 files, select ```selected``` for generating some of them.

    __Options__: ```all```, ```selected```.

* __outputs__: < ```list``` >
    * Specifically chooses the data structures of interest 

        __Options__: ```db```, ```coord```, ```rays```.

### blensor

Generate images or lidar using blensor.

> Parameters

* __enabled__: < ```boolean``` >
    * Enable/disable blensor usage.

* __outputs__: < ```list``` of options >
    * Chooses desired outputs from blensor. 

        __Options for list__: ```lidar```, ```images```.

### post_processing

Choose which post processing generate. 
- Beams: simulate MIMO channels from hdf5 rays information using geometric channel approach defined at David Tse's book - Fundamentals of Wireless Communications at 7.3.2 - MIMO multipath channel. This generates .npz files for best beam pair, the combined channels and the channel matrixes.
- Image: Refine generated images by marking receiver positions and bounding boxes.
- Lidar: Generate voxels from lidar point clouds.

> Parameters

* __enabled__: < ```boolean``` >
    * Enable/disable post processing generating.

* __which__: < ```option``` >
    * Choose post processing to make. Select ```all``` for beams, lidar and images, select ```selected``` for generating some of them.
    
        __Options__: ```all```, ```selected```.

* __outputs__: < ```list``` of options >
    * Choose desired post processings. 

        __Options for list__: ```beams```, ```lidar```, ```image```.

### validation

Check consistency of valid and invalid channels from csv, hdf5 and beam files. 

> Parameters

* __run_checkup__: < ```boolean``` >
    * Enable/disable validation check.

## Configuring rmt

This configuration refers to configuring Raymobtime (RMT) samppling methodology.

> Parameters

* __enabled__: < ```boolean``` >
    * Enable/disable raymobtime methodology.

        Obs: when disabled refers to an isolated simulation, where no mobile objects exist, just an interest on simulate a single communication scenario and also use other available features.

* __scenes_per_episode__: < ```integer``` >
    * Sets the number of scenes per episode. 
    
        Obs: The inexistence of receivers in a given scene from episode cause a premature episode end, with less scenes then set here.

* __time_between_episodes__: < ```float``` >
    * Sets the time between episodes in seconds. 

        Obs: The number needs to be multiple of scene time step.

* __sampling_parameters__: < ```[start, end, time_step]``` >
    
    * ```start``` sets from which valid scene (sufficient vehicles) start, time between episodes is considered.
    
    * ```end``` sets the total number of runs (sum of all scenes from each episode).
    
    * ```time_step``` sets the time between scenes.

* __features__: 
    Configures features relative to RMT methodology
    
    > Parameters
    
    * __fixed_receivers__: < ```boolean``` >
        * Sets if the receiver antennas will be fixed, not attached to a vehicle. 
    
    * __vehicles_template__: < ```boolean``` >
        * If is desired use a low poly 3D modelled templates with scatter propperties for vehicles or just use simple boxes with scatter propperties.

## Configuring sumo

Sets sumo files and random seed for traffic flows generating.    

> Parameters

* __seed__: < ```integer``` >
    * Sets random seed for traffic flows generating.

* __bin__: < ```path``` >
    * Sets path for SUMO binary in order to execute it. 

* __cfg__: < ```string``` >
    * Sets the name of the sumo configuration file from your respective scenario.

        Obs: This file needs to be at your base files, most precisely in sumo folder. The file is a .sumocfg type.

## Configuring ray-tracing
Configure parameters relative to positioning communication elements.

> Parameters

* __use_pedestrians__: < ```boolean``` >
    * Sets if the antennas will be placed only at pedestrians.

* __use_drone__:

    Configures drone usage.

    > Parameters

    * __enabled__: < ```boolean``` >
        * Sets if the antennas will be placed only at drones.

    * __altitude__: < ```float``` >
        * Sets drones flying altitude in meters.

* __receivers_per_episode__: < ```integer``` >
    * Sets the number of receivers to exist at episode beginning.

* __transmitters_per_episode__: < ```integer``` >
    * Sets the number of transmitters to exist at episode beginning.

* __v2v__:

    Configures vehicle to vehicle communication.
    
    > Parameters 
    
    * __enabled__: < ```boolean``` >
        *  Enable/disable v2v positioning, where transmitters and receivers are attached to mobile objects.
    
    * __clesest_vehicles__:
        
        From potential receiver vehicles in area, choose the ones with closest euclidian distance relative to the transmitter to be receivers. Obs: This works only for one transmitter simulation.

        > Parameters

        * __enabled__: < ```boolean``` >
            * Enable/disable feature.

        * __n_of_vehicles__: < ```integer``` >
            * Number of vehicles to be chosen.

                Obs: Needs to be a smaller number then receivers_per_episode.
    
    * __wireless_insite__:
        
        Configuration of wireless insite files.

        > Parameters

        * __software_path__: < ```PATH``` >
            * Sets path for Wireless Insite binary in order to execute it. 

        * __LICENSE_FILE__: < ```LICENSE``` >
            * Sets Wireless Insite license. 

        * __base_files_names__:
            
            Sets names used at Wireless Insite base files.

            > Parameters

            * __study_area_name__: < ```string``` >
                * Name of Wireless Insite study area.

            * __tx_name__: < ```string``` >
                * Name defined for transmitter element at Wireless Insite.

            * __rx_name__: < ```string``` >
                * Name defined for receiver element at Wireless Insite.

            * __setup_name__: < ```string``` >
                * Name of Wireless Insite project.

            * __vehicles_name__: < ```string``` >
                * Name of wireless insite template object used for representing vehicles.


## Configuring blensor_options
Configure parameters for using blensor.

> Parameters

* __path_to_scenario_blend__: < ```PATH``` >
    * Sets relative path from repository root to the 3D model of scenario .blend file.

        Obs: This file needs to use the old binary blender files, such as from 2.29b blencer version.

* __path_to_vehicles_blend__: < ```PATH``` >
    * Sets relative path from repository root to the 3D model of vehicles .blend file.

* __path_blensor_image__: < ```PATH``` >
    * Sets relative path from repository root to blensor.AppImage, in order to execute it.

* __image_options__: 
    Configures generation of images using blensor. 

    > Parameters

    * __UE_camera__: < ```boolean``` >
        * Enable/disable generation of images from receiver point of view.

        Obs: Always generate 4 images from receiver view. The index 1, 2, 3 and 4 at images nomenclature refers to left, backwards, frontwards and right points of view from vehicle perspective, respectively.

    * __BS_camera__: < ```boolean``` >
        * Enable/disable generation of images from transmitter point of view.

                Obs: Only fixed?

    * __n_camera_BS__: < ```integer``` >
        * Chooses how many images generate from transmitter view point.

                manually set cameras

## Configuring data_processing
Configures generation of SQL, csv and hdf5 files.

Obs: For SQL and hdf5 there is no configuration available, just for csv at the moment.

> Parameters

* __area_of_analyses__: 

    Delimits an area where vehicles need to be to include it at csv.

    > Parameters

    * __enabled__: < ```boolean``` >
        * Enable/disable area delimitation.
    * __limits__: < ```[x1_float, y1_float, x2_float, y2_float]``` >
        * Defines area delimitation. It is a square, x1 and y1 are the left inferior coordinates, x2 and y2 are the right superior coordinates.

## Configuring post_processing
Configures MIMO, images marking and lidar voxels post processings.

Obs: For images there is no adicional configuration available, it just generates images with receiver positions marked and bounding boxes from transmitter images.

> Parameters
* __mimo__:

    Simulates MIMO channels from ray-tracing outputs stored in hdf5 files using the geometric narrowband channel model. The generated outputs include channel matrices, combined channels and optimal beam pair information.

    This implementation follows the methodology commonly adopted in mmWave communication systems and described in David Tse's *Fundamentals of Wireless Communication*, Section 7.3.2. The channel is reconstructed from the multipath components provided by the ray-tracing simulator, including path gains, phases, angles of departure and angles of arrival.

    The geometric channel model is expressed as

    $$
    \mathbf{H} =
    \sum_{l=1}^{L}
    \alpha_l
    \mathbf{a}_r(\phi_l^A,\theta_l^A)
    \mathbf{a}_t^{H}(\phi_l^D,\theta_l^D),
    $$

    where:

    - $L$ is the number of propagation paths;
    - $\alpha_l$ is the complex gain of the $l$-th path;
    - $\phi$ and $\theta$ are the azimuth and elevation angles;
    - $A$ and $D$ indicate arrival and departure, respectively;
    - $\mathbf{a}_r$ and $\mathbf{a}_t$ are the receiver and transmitter steering vectors.

    The transmitter and receiver are modeled as Uniform Planar Arrays (UPA) containing $N_{Tx}$ and $N_{Rx}$ antenna elements, respectively. The steering vectors are constructed as

    $$
    \mathbf{a}(\phi,\theta)
    =
    \frac{1}{\sqrt{N_xN_y}}
    \left(
    \begin{bmatrix}
    1 \\
    e^{-j\omega_x} \\
    \vdots \\
    e^{-j(N_x-1)\omega_x}
    \end{bmatrix}
    \otimes
    \begin{bmatrix}
    1 \\
    e^{-j\omega_y} \\
    \vdots \\
    e^{-j(N_y-1)\omega_y}
    \end{bmatrix}
    \right),
    $$

    where:

    - $N_x$ is the number of antenna elements along the x dimension;
    - $N_y$ is the number of antenna elements along the y dimension;
    - $\otimes$ denotes the Kronecker product.

    The spatial frequencies are computed as

    $$
    \omega_x
    =
    2\pi d
    \sin(\theta)
    \cos(\phi),
    $$

    and

    $$
    \omega_y
    =
    2\pi d
    \sin(\theta)
    \sin(\phi),
    $$

    where:

    - $d$ is the antenna spacing normalized by the wavelength;
    - $\phi$ is the azimuth angle;
    - $\theta$ is the elevation angle.

    Beamforming is performed through precoding and combining vectors,

    $$
    y_i
    =
    \mathbf{w}_i^{H}
    \mathbf{H}
    \mathbf{f}_i,
    $$

    where:

    - $y_i$ is the equivalent channel associated with beam pair $i$;
    - $\mathbf{f}_i$ is the precoding vector;
    - $\mathbf{w}_i$ is the combining vector.

    By default, Raymobtime generates DFT-based codebooks. Independent DFT codebooks are first generated for the horizontal and vertical dimensions of the planar array and then combined using a Kronecker product. This procedure creates a two-dimensional beam codebook covering both azimuth and elevation domains.

    All beam pairs are evaluated and the optimal beam index is selected according to

    $$
    \hat{i}_{optimal}
    =
    \underset{i \in \{1,\dots,N_c\}}
    {\operatorname{argmax}}
    |y_i|,
    $$

    where:

    - $N_c$ is the total number of candidate beam pairs in the codebook;
    - $y_i$ is the equivalent channel corresponding to beam pair $i$.

    The generated outputs are:

    - **beam_output**: `.npz` file containing the optimal beam pair labels $\hat{i}_{optimal}$;
    - **channel_output**: `.npz` file containing the equivalent channel magnitudes $|\mathbf{w}_i^{H}\mathbf{H}\mathbf{f}_i|$;
    - **hmatrix**: `.npz` file containing the channel matrices $\mathbf{H}$.


    > Parameters
    * __import_precoding__: < ```PATH``` or ```false``` >
        * Imports a predefined precoding codebook from a `.npy` file.
        * If set to ```false```, a DFT-based codebook is generated automatically.

    * __import_channels__: < ```PATH``` or ```false``` >
        * Imports a channel matrix from an external source.
        * Typically used for loading channel matrices previously generated from Wireless InSite outputs (Hmatrix).

    * __import_combining__: < ```PATH``` or ```false``` >
        * Imports a predefined combining codebook from a `.npy` file.
        * If set to ```false```, a DFT-based codebook is generated automatically.


    * __antenna_array_expansion__:

        Configures the antenna array dimensions used to construct transmitter and receiver arrays.

        > Parameters

        * __Tx__: < ```[x, y]``` >
            * Defines the transmitter antenna array dimensions.
            * The array is expanded following the internal convention of y and x axes.

        * __Rx__: < ```[x, y]``` >
            * Defines the receiver antenna array dimensions.
            * The array is expanded following the internal convention of y and x axes.

        * __normalized_antenna_distance__: < ```float``` >
            * Normalized spacing between adjacent antenna elements.
            * A value of ```0.5``` corresponds to half-wavelength spacing, which is commonly adopted in literature.

    * __array_rotation__:

        Applies rotations to transmitter and receiver antenna arrays.

        > Parameters

        * __Tx__: < ```[alpha, beta, gamma]``` >
            * Rotation angles applied to the transmitter array.
            * Rotations follow the internal convention of z, y and x axes.

        * __Rx__: < ```[alpha, beta, gamma]``` >
            * Rotation angles applied to the receiver array.
            * Rotations follow the internal convention of z, y and x axes.
        
* __cartesian_lidar_matrix__:
    
    Generates voxelized representations from LiDAR point clouds.

    The voxelization process can be performed either in Cartesian or spherical coordinates, producing occupancy matrices suitable for machine learning applications.

    > Parameters

    * __coordinate_system__: < ```option``` >
        * Selects the coordinate system used during voxelization.

            __Options__: ```cartesian```, ```spherical```.

     * __QP__:

        Defines the Cartesian voxel grid parameters.

        > Parameters

        * __step__: < ```[x, y, z]``` >
            * Resolution of each voxel along the x, y and z axes.

        * __min__: < ```[x, y, z]``` >
            * Minimum coordinate limits of the voxel grid.

        * __max__: < ```[x, y, z]``` >
            * Maximum coordinate limits of the voxel grid.

    * __QPsph__:

         Defines the spherical voxel grid parameters.

        > Parameters

        * __step__: < ```[r, phi, theta]``` >
            * Resolution of each voxel along radial and angular dimensions.

        * __min__: < ```[r, phi, theta]``` >
            * Minimum coordinate limits of the spherical grid.

        * __max__: < ```[r, phi, theta]``` >
            * Maximum coordinate limits of the spherical grid.

    * __Tx_position__: < ```[x, y, z]``` >
        * Defines the transmitter position used as reference during voxelization.

    * __max_dist_LIDAR__: < ```float``` >
        * Maximum LiDAR detection distance considered during voxelization.

    * __type_data__: < ```option``` >
        * Defines the dimensionality of the generated voxel representation.

            __Options__: ```2D```, ```3D```.

## Notes

There is no need to configure a module if its outputs are not required and it is not a prerequisite for another module.

For example, the post-processing module does not need to be configured if beam, image or LiDAR post-processed outputs are not desired.

## Module Requirements

The following table summarizes the dependencies between generated outputs and Raymobtime modules.

| Output | Required Modules |
|----------|----------|
| Coordinates | Mobility + Data Processing |
| Rays | Mobility + Ray Tracing + Data Processing |
| Images | Mobility + Data Processing + Blensor |
| LiDAR | Mobility + Data Processing + Blensor |
| Beams | Ray Tracing + Data Processing + Post Processing |

# Running Raymobtime
With base correctly set and [YAML](/config.yaml) properly configured, go at repository root and run 

```
uv run raymobtime
```