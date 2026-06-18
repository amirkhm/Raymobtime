# 💻 Raymobtime Setup Guide

## Overview

This document describes how to set up a clean Raymobtime environment from scratch on Linux. The setup has been tested on Linux and uses `uv` for Python dependency management.

> **Note:** Depending on the intended Raymobtime usage, not all external software packages described in this guide need to be installed.

Raymobtime acts as an orchestrator for several external simulation tools. Use this document as a general installation guide and follow the corresponding software links for detailed installation instructions.

# 📦 Requirements

## ⚓ Recommended Operating System

Raymobtime has been developed and tested primarily on Linux.

Recommended distributions:

* Ubuntu 22.04 LTS;
* Ubuntu 24.04 LTS.

<!--

## Hardware Requirements

| Component | Recommended |
|---|---|
| CPU | 4 or more cores |
| RAM | 16 GB or more |
| Storage | 20 GB or more of free space |
| GPU | Optional, but recommended for Blender and Wireless InSite workflows |

-->

## 🚦 Mobility Software

Mobility software is required to generate the positions and movement of dynamic objects over time.

### Simulation of Urban MObility — SUMO

SUMO is an open-source traffic simulation framework used to generate vehicle and pedestrian mobility.

* Recommended version: latest stable release;
* Tested versions: 1.18 and 1.20.

Installation instructions are available in the official [SUMO installation guide](https://sumo.dlr.de/docs/Installing/index.html).

After installation, verify that SUMO is available:

```bash
sumo --version
```

The command should display the installed SUMO version without errors.

## 📡 Ray-Tracing Simulator

<<<<<<< HEAD
A ray-tracing simulator is required to generate spatially consistent wireless propagation channels.

### Wireless InSite

Wireless InSite is a commercial electromagnetic ray-tracing simulator used by Raymobtime to generate wireless propagation data.

* Wireless InSite is not open-source software;
* a valid license is required;
* at the time of writing, the graphical interface is not available for Linux;
* Raymobtime currently supports Wireless InSite 3.3.
=======
Raymobtime supports Wireless InSite version 3.2 and 3.3.
>>>>>>> 046706ea3171ba4dfde3764413a986b8af9df1ba

Install [Wireless InSite](https://www.remcom.com/wireless-insite-propagation-software) according to the vendor instructions.

After installation:

* verify that the software runs correctly;
* record the path to the Wireless InSite executable;
* confirm that the configured license is active;
* verify that a test propagation simulation can be executed.

> **Note:** Since Wireless InSite is normally configured through its graphical interface on Windows, the base scenario may need to be prepared on Windows before the simulation files are transferred to the Linux environment used by Raymobtime.

## 🎥 3D Computer Graphics Software

Blender is required to prepare three-dimensional scenarios and to support the RGB image and LiDAR features.

### Blender

Blender is an open-source application for 3D modeling, scene editing, rendering, animation, and simulation.

Multiple add-ons are used by the Raymobtime workflow. Pay attention to the Blender version required by each add-on. Older Blender versions may not be able to open `.blend` files saved by newer versions because of changes in the binary file format.

Supported versions:

* [Blender 2.79b](https://www.blender.org/download/releases/2-79/);
* [Blender 3.6.9](https://www.blender.org/download/releases/3-6/).

### Add-ons for Blender 2.79b

* [Blosm](https://github.com/vvoovv/blosm): imports OpenStreetMap data into Blender.

  * [Blosm 2.4.21](https://github.com/vvoovv/blosm/releases/tag/v2.4.21) is compatible with Blender 2.79.

* [Blensor](https://www.blensor.org/pages/downloads.html): provides simulated sensor models for Blender. In Raymobtime, Blensor is used primarily to generate LiDAR point clouds.

  * The project-compatible version is available through the [LASSE Nextcloud](https://nextcloud.lasseufpa.org/apps/files/files/473423?dir=/5GM/Blender).

### Add-ons for Blender 3.6.9

* [Blosm](https://github.com/vvoovv/blosm): imports OpenStreetMap data into Blender.

  * Blosm 2.7.9 is compatible with Blender 3.6.9.

* [Super Batch Export](https://github.com/mrtripie/Blender-Super-Batch-Export): automates the export of multiple geometries, including COLLADA files used during Wireless InSite scenario preparation.

> **Note:** Blender 3.6.9 is primarily used for scenario modeling, cleaning, and geometry export. Blender 2.79b is required for compatibility with Blensor and other legacy tools.

## 🟣 uv

`uv` is the Python package and environment manager used by Raymobtime.

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal or reload the shell configuration if the `uv` command is not immediately available.

Verify the installation:

```bash
uv --version
```

## 🚗 Raymobtime

Raymobtime is the Python-based orchestrator that integrates the mobility, ray-tracing, RGB image, LiDAR, and post-processing stages.

Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

To use a specific release, check out the corresponding tag:

```bash
git checkout <tag-name>
```

Synchronize the Python version and project dependencies:

```bash
uv sync
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Verify that the Raymobtime command is available:

```bash
raymobtime --help
```

If the project is executed directly through Python instead of the command-line entry point, use the corresponding project execution command.

---

# ⚙️ Configuration

To use the installed external software with Raymobtime, configure the corresponding executable paths and license information in the project [YAML configuration file](../config.yaml).

The configuration file is located at the repository root:

```text
config.yaml
```

## 📂 Path Configuration

The following paths must be adjusted according to the local installation:

```yaml
sumo:
  bin: <sumo binary path>

ray_tracing:
  wireless_insite:
    software_path: <Wireless InSite binary path>
    LICENSE_FILE: REMCOMINC_LICENSE_FILE=<your license>

blensor_options:
  path_blensor_image: <Blensor AppImage path>
```

Replace the placeholder values with valid absolute paths.

For example:

```yaml
sumo:
  bin: /usr/bin/sumo

ray_tracing:
  wireless_insite:
    software_path: /opt/remcom/bin/x3d
    LICENSE_FILE: REMCOMINC_LICENSE_FILE=<your license>

blensor_options:
  path_blensor_image: /opt/blensor/blensor.AppImage
```

The exact configuration fields may depend on the selected Raymobtime version and enabled features.

> **Note:** Only the paths associated with the enabled features need to be configured. For example, Blensor is not required when LiDAR generation is disabled.

## Testing the Setup

To verify that the environment is working correctly, select an existing base scenario and execute the pipeline with the desired outputs enabled.

The directory:

```text
data/rosslyn/
```

contains base files that can be used to test the Raymobtime pipeline.

Before executing the test, confirm that:

* the required software is installed;
* the executable paths in `config.yaml` are correct;
* the Wireless InSite license is active;
* the selected base scenario exists;
* the requested features are compatible with the installed software;
* the output directories are writable.

The following documents describe the next steps:

* [Dataset Generation Guide](3-DatasetCreation.md): explains how to configure `config.yaml` and generate the desired outputs from an existing base scenario;
* [Base Scenario Creation](2-BaseCreation.md): explains how to create and configure a new base scenario.

<!--

# ⚠️ Troubleshooting

## Common Issues

-->

# Version Summary

| Component       | Version                         |
| --------------- | ------------------------------- |
| Python          | 3.8.20                          |
| uv              | Latest stable release           |
| SUMO            | 1.18 or 1.20                    |
| Wireless InSite | 3.3                             |
| Blender         | 3.6.9 or 2.79b                  |
| Blosm           | 2.7.9 or 2.4.21                 |
| Blensor         | Project-compatible version      |
| Raymobtime      | Commit or tag `<commit-or-tag>` |
