# Overview

This document is a tutorial guide on how generating datasets using raymobtime.

## General base concept 
The core idea of generated datasets is simulate a scenario where communication happens.

For that it is necessary define where it happens, that is a 3D scenario, how is the environment state, who are the communication elements and where they are positioned. 

The mobility simulator is responsible por inform where mobile objects are placed and respective orientation and speed.

The raytracing simulator is responsible for characterizing radio  communication elements and the environment, in order to simulate propagation characteristics of eletromagnetic fields at the communication scenario.

The 3D computer graphics software is responsible for rendering images taken from positions of interest at refered 3D environment and also simulate a lidar sensor. The positions of interest tend to be the receiver or transmitter positions.

>Note that some in some moments User Equipament (UE) and Base Station (BS) are used to refer to receiver and transmiter elements, respectively. 

All This context that refers to where, how and who communicates in a given situation is here refered to a base.

If in your kind of interest, [how create a base](/doc/2-BaseCreation.md) is a doc that gives a tutorial on how creating your own base, with your desired circunstances.

## What expect from dataset

Since you already have a base where you plan communication happen, you may question yourself: 

> 🤔 What kind of outputs am i generating with raymobtime?

Following the [methodology](/README.md) described, time sampples of the communication system are taken. At each sample is known the state of elements of interest, as described below:

* Cartesian coordinates of mobile objects
* Cartesian coordinates of transmiter and receiver elements
* Ray-tracing outputs
    * Propagation paths.
    * Received power.
    * Complex E-fields.
    * Complex impulse response.
    * Delay spread.
* Images of refered time instant from UE and BS points of view.
* Lidar point clouds obtained at receivers position
* Post processed rt outputs
    * Multiple Input Multiple Output (MIMO) communication system using geometric channel aproach.
* Post processed image outputs
    * Images from transmitter point of view with bounding boxes at receivers.
* Post processed lidar outputs
    * Voxelized 2D/3D lidar matrixes using cartesian/spherical coordinates using receiver as reference point.

The use of this data may vary depending on your focus, but it is commonly used for machine learning in beam selection or beam tracking problems.

# How generate desired outputs

Considering you already have a base, all necessary configurations are done at [YAML](/config.yaml) of configuration. This section describes how configure the [YAML](/config.yaml) and what are the implemented features.

The structure the file folows as below

    base_config: (...)
    pipeline: (...)
    rmt: (...)
    sumo: (...)
    ray-tracing: (...)
    blensor_options: (...)
    post_processing: (...)

## Configurating __base_config__

First, you need to refer to your respective base, so configure base_config entries.

* __scenario__: < ```string``` >
    * Base name at [data](/data/) folder
* __output_name__: < ```string``` >
    * Set a name for your simulation, this is very useful when you have to configure many variations of outputs using the same base.
* __yaml_output__: < ```boolean``` >
    * Save the a copy of [YAML](/config.yaml) at the output folder, in order to document the configuration used to achieve that outputs.
* __logging_level__: < ```option``` >
    * Sets the logging level, in order to folow the status of simulation in real time. 

    __Options__: ```debug```, ```info```, ```warning```, ```error```, ```critical```, ```NONE```
* __resume__: < ```boolean``` >
    * Skip steps already concluded, if false remember to clean previous outputs.
* __clean_previous__: < ```list``` of options , empty ```list``` >
    * Clean listed outputs in order to re-run and the results. It turns to be important when something in pipeline changes.
    * __Options for list__: ```mobility```, ```rt```, ```db```, ```coord```, ```hdf5```, ```blensor_lidar```, ```blensor_images```, ```post_lidar```, ```post_images```, ```beams```.

## Configurating pipeline
The way raymobtime was constructed there is an actual pipeline followed, where an order of events happen. The logic will be here explicited.

### mobility
In case of existence of mobile objects, a mobility tool is needed to inform where the objects are placed at a refered instant also the orientations and speed.

The objects position obtaining at a given instant here is called placement. Given the interest of communication channel elements, they may or not be atacched to mobile objects. This context refers to the difference of an antenna with fixed position or fixed to a mobile structure, that carry and consequently changes the antenna position according to object designed movement.

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
Used for calculate multipath components, in order to simulate communication channels with spatial concistency. 
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
- Beams: simulate MIMO channels from hdf5 rays information using geometric channel aproach defined at David Tse's book - Fundamentals of Wireless Communications at 7.3.2 - MIMO multipath channel. This generates .npz files for best beam pair, the combined channels and the channel matrixes.
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
Check concistency of valid and invalid channels from csv, hdf5 and beam files. 
> Parameters
* __run_checkup__: < ```boolean``` >
    * Enable/disable validation check.

## Configurating rmt
## Configurating sumo
## Configurating ray-tracing
## Configurating blensor_options
## Configurating post_processing

```
## name 
General and high level explanation
- place referencial theoric according
> parameters
entry : < option >
    short explanation
    options: <option>, <option>, ..., <option>.
```


## Notes

There is no need of configure a certain module if you don't desire it's outputs and it's not pre-requisite for an other module work, eg: post-processing module.

## Modules requisites

| Output | Required Modules |
| - | - |
| Coordinates | Mobility + Data Processing |
| Rays        | Mobility + Ray Tracing + Data Processing |
| Images      | Mobility + Data Processing + Blensor |
| LiDAR       | Mobility + Data Processing + Blensor |
| Beams       | Ray Tracing + Post Processing |

# Running Raymobtime
With base correctly set and [YAML](/config.yaml) properly configured, go at repository root and run 

```
uv run raymobtime
```

# Datsets stucture