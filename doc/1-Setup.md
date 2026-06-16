# Raymobtime Setup Guide

## Overview

This document describes how to set up a clean Raymobtime environment from scratch on Linux.

The setup has been tested on Linux and uses `uv` for Python dependency management.

## System Requirements

### Recommended Operating System

* Linux (tested environment)
* Recommended distributions:

  * Ubuntu 22.04 LTS
  * Ubuntu 24.04 LTS

### Hardware Requirements

| Component | Recommended                                                      |
| --------- | ---------------------------------------------------------------- |
| CPU       | 4+ cores                                                         |
| RAM       | 16 GB or more                                                    |
| Storage   | 20+ GB free space                                                |
| GPU       | Optional (recommended for Blender and Wireless InSite workflows) |

---

## Clone the Repository

Clone the latest stable state of the main branch.

```bash
git clone <repository-url>
cd <repository-name>
```

To identify the exact commit currently used for validation:

```bash
git checkout main
git pull
git rev-parse HEAD
```

This command prints the commit hash corresponding to the validated project state.

To checkout a specific validated commit:

```bash
git checkout <commit-hash>
```

---

## Installing UV

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:

```bash
uv --version
```

---

## Creating the Environment

Synchronize dependencies:

```bash
uv sync
```

Activate the environment:

```bash
source .venv/bin/activate
```

Verify installation:

The project currently uses: Python 3.8.20.

Verify:

```bash
uv run python --version
```

---

# External Dependencies

The following third-party software must be installed.

## SUMO

Traffic simulation framework.
Tested at versions 1.18 and 1.20.

Follow the steps described at sumo
[documentation](https://sumo-dlr-de.translate.goog/docs/Installing/index.html?_x_tr_sl=en&_x_tr_tl=pt&_x_tr_hl=pt&_x_tr_pto=tc)
for installing on linux.


Verify installation:

```bash
sumo --version
```

---

## Wireless InSite (v3.3)

Ray tracing simulator. 

Obs: 
- This is not a open source software.
- At the moment of this documentation there is no graphical interface available for linux.

Install Wireless InSite version 3.3 according to the vendor instructions.

After installation, verify:

* Wireless InSite launches correctly.
* The executable path: wireless-insite/remcom.
* Required licenses are active.

---

## Blender

Supported versions:

[Blender 3.6.9](https://www.blender.org/download/releases/3-6/)

[Blender 2.79b](https://www.blender.org/download/releases/2-79/)


---

## Blender Super Batch Export

Repository:

https://github.com/mrtripie/Blender-Super-Batch-Export

Install as a Blender add-on.

---

## Blosm

OpenStreetMap importer for Blender.

Supported version:

* Blosm 2.4.21
* Compatible with Blender 2.79

Download:

https://github.com/vvoovv/blosm/releases/tag/v2.4.21

Install as a Blender add-on.

---

## Blensor

Synthetic LiDAR simulator.

Download:

https://nextcloud.lasseufpa.org/apps/files/files/473423?dir=/5GM/Blender

Install according to the project instructions.

---

# Configuration

## YAML Configuration

The following paths must be configured in the Raymobtime YAML file.

Example:

```yaml
wireless_insite_path: /path/to/wireless_insite

sumo_path: /path/to/sumo

blender_path: /path/to/blender

blensor_path: /path/to/blensor
```

Update all paths according to your local installation.

---

# Verification

Run a minimal scenario to verify that:

* SUMO executes correctly.
* Wireless InSite executes correctly.
* Blender launches correctly.
* Blensor generates point clouds.
* Raymobtime pipeline completes successfully.

---

# Troubleshooting

## Common Issues

### Missing executable

Check configured paths in the YAML file.

### Python dependencies not found

Re-run:

```bash
uv sync
```

### Wireless InSite execution failure

Verify installation and licensing.

### Blender add-ons unavailable

Confirm that:

* Blosm is installed.
* Blender Super Batch Export is installed.
* Blensor is installed.

---

# Version Summary

| Component       | Version                |
| --------------- | ---------------------- |
| Python          | 3.8.20                 |
| uv              | latest                 |
| SUMO            | 1.20                   |
| Wireless InSite | 3.3                    |
| Blender         | 3.6.9 or 2.79b         |
| Blosm           | 2.4.21                 |
| Blensor         | project version        |
| Raymobtime      | commit `<commit-hash>` |

```
```
