# 💻 Raymobtime Setup Guide
## Overview

* This document describes how to set up a clean Raymobtime environment from scratch on Linux.
* The setup has been tested on Linux and uses `uv` for Python dependency management.
> 📓  Note: Depending on your intend on raymmobtime usage, not all installations are needed.

Raymobtime works as orchestrator of some external softwares, use this doc as a guide for installation and find respective software links.


# 📦 Requirements

## ⚓ Recommended SO

* Linux (tested environment)
* Recommended distributions:

  * Ubuntu 22.04 LTS
  * Ubuntu 24.04 LTS

<!-- 

 Hardware Requirements

| Component | Recommended                                                      |
| --------- | ---------------------------------------------------------------- |
| CPU       | 4+ cores                                                         |
| RAM       | 16 GB or more                                                    |
| Storage   | 20+ GB free space                                                |
| GPU       | Optional (recommended for Blender and Wireless InSite workflows) |

-->

## 🚦 Mobility software
Necessary for implementing positional changes over time in objects.
### Simulator of Urban Mobility (SUMO)

SUMO is a traffic simulation framework.
  * This is an open source software.
  * Version recommended: latest.
  * Tested versions: 1.18, 1.20.

The installation steps are described at
[sumo installing](https://sumo.dlr.de/docs/Installing/index.html).

Verify version:

```bash
sumo --version
```

## 🔣 Ray-tracing simulator
Necessary for simulate spatial consistent channels.
### Wireless Insite

Wireless Insite is a ray-tracing simulator. 
* This is not a open source software.
* The software needs license to use.
* At the moment of this documentation there is no graphical interface available for linux.

Raymobtime supports Wireless InSite version 3.3.

Install [Wireless InSite](https://www.remcom.com/wireless-insite-propagation-software) according to the vendor instructions.

After installation:

* Verify that the software is working properly
* Keep the executable path.
* Verify that the license used is active.

## 🌠 3D computer graphics software
Necessary to manipulate 3D models and correct work of lidar and image features.
### Blender

Software for modeling, sculpting, and rigging to animation, simulation, rendering, and video editing.

  * This is an open source software.
  * There are multiple addons available, very useful to acess many funcionalities.
  * Pay attention at blender version when using. At blender development there was a moment were the .blend binary file format changed, so newer binary are not recognized by this old versions.

Supported versions:
* [Blender 2.79b](https://www.blender.org/download/releases/2-79/)
* [Blender 3.6.9](https://www.blender.org/download/releases/3-6/)

Addons for Blender 2.79b:
* [Blosm](https://github.com/vvoovv/blosm): OpenStreetMap importer for Blender. 
  * [Version 2.4.21](https://github.com/vvoovv/blosm/releases/tag/v2.4.21) is compatible with blender 2.79.
* [Blensor](https://www.blensor.org/pages/downloads.html): Binary that implement muitiple sensors at blender. Here Blensor is used to generate images and lidar point clouds. [Nextcloud download](https://nextcloud.lasseufpa.org/apps/files/files/473423?dir=/5GM/Blender)

Addons for Blender 3.6.9:
* [Blosm](https://github.com/vvoovv/blosm): OpenStreetMap importer for Blender. 
  * Version 2.7.9 is compatible with blender 3.6.9.
* [Super Batch Export](https://github.com/mrtripie/Blender-Super-Batch-Export): Used to export multiple geometry as collada.

## 🟣 UV

Python packet manager used at raymobtime.

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:

```bash
uv --version
```

## 🚗 Raymobtime

Python orchestrator repository.

Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

Checkout to specific tag:

```bash
git checkout <tag-name>
```

Synchronize uv dependencies:

```bash
uv sync
```

Activate the environment:

```bash
source .venv/bin/activate
```

---

# ⚙️ Configuration

For using the installed softwares at raymobtime it is necessary configure paths at config.yaml file. 

## 📂 Path Configuration

The following paths must be configured in the Raymobtime config.yaml file according to your local installation. This file is located at repository root.

```yaml
sumo:
  bin: <sumo binary path>

ray_tracing:
  wireless_insite:
    software_path: <remcom binary path>
    LICENSE_FILE: REMCOMINC_LICENSE_FILE=<your license>

blensor_options:
  path_blensor_image: <blensor.AppImage binary path>
```

<!-- 
## ⚠️ Troubleshooting
## Common Issues
-->

# Version Summary

| Component       | Version                |
| --------------- | ---------------------- |
| Python          | 3.8.20                 |
| uv              | latest                 |
| SUMO            | 1.20                   |
| Wireless InSite | 3.3                    |
| Blender         | 3.6.9 or 2.79b         |
| Blosm           | 2.7.9 or 2.4.21        |
| Blensor         | project version        |
| Raymobtime      | commit `<commit-hash>` |
