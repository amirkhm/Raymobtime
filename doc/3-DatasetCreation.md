# Dataset creation
## Overview

This document is a tutorial guide on how generating datasets using raymobtime.

### General base concept 
The core idea of generated datasets is simulate a scenario where communication happens.

For that it is necessary define where it happens, that is a 3D scenario, how is the environment state, who are the communication elements and where they are positioned. 

The mobility simulator is responsible por inform where mobile objects are placed and respective orientation and speed.

The raytracing simulator is responsible for characterizing radio  communication elements and the environment, in order to simulate propagation characteristics of eletromagnetic fields at the communication scenario.

The 3D computer graphics software is responsible for rendering images taken from positions of interest at refered 3D environment and also simulate a lidar sensor. The positions of interest tend to be the receiver or transmitter positions.

>Note that some in some moments User Equipament (UE) and Base Station (BS) are used to refer to receiver and transmiter elements, respectively. 

All This context that refers to where, how and who communicates in a given situation is here refered to a base.

If in your kind of interest, [how create a base](/doc/2-BaseCreation.md) is a doc that gives a tutorial on how creating your own base, with your desired circunstances.

### What expect from dataset

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

## How generate desired outputs

Considering you already have a base, all necessary configurations are done at [YAML](/config.yaml) of configuration.

The structure of this file folows as below

    base_config: (...)
    pipeline: (...)
    rmt: (...)
    sumo: (...)
    ray-tracing: (...)
    blensor_options: (...)
    post_processing: (...)

First, you need to refer to your respective base, so configure base_config entries.
* scenario: < Simulation identifier name >
    * Base name at [data](/data/) folder
* output_name: < Simulation identifier name >
    * Set a name for your simulation, this is very useful when you have to configure many variations of outputs using the same base.
* yaml_output: < true or false >
    * Save the a copy of [YAML](/config.yaml) at the output folder, in order to document the configuration used to achieve that outputs.
* logging_level: < debug, info, warning, error, critical, NONE >
    * Sets the logging level, in order to folow the status of simulation in real time. 
* resume: < true or false >
    * Skip steps already concluded, if false remember to clean previous outputs.
* clean_previous: < list, empty list or just nothing >
    * Clean listed outputs in order to re-run and the results. It turns to be important when something in pipeline changes.
    * Possible elements in list: mobility, rt, db, coord, hdf5, blensor_lidar, blensor_images, post_lidar, post_images, beams.
    

remove result folders before running

The first tag of [YAML](/config.yaml): base_config has the following  entries
    

Note: There is no need of configure a certain module if you don't desire it's outputs and it's not pre-requisite for an other module work, such as post-processing module.



First 

___
Features expanation at yaml
place referencial theoric according
___
Since you have a base
___
 