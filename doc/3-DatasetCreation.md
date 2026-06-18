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

# Dataset concept

Since you already have a base where you plan communication happen, you may question yourself: 
> 🤔 What kind of outputs i am generating with raymobtime?

# Start

Since


# how config yaml

# how gen outputs