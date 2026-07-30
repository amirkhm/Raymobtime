# Adopted Coding Style

This document defines the recommended development practices for contributing to Raymobtime. The objective is to preserve code organization, configuration consistency, reproducibility, and compatibility across the simulation pipeline.

## 1. Configuration Management

All user-configurable parameters must be defined through the Raymobtime configuration system.

When adding a new configurable parameter:

1. add the parameter to the root `config.yaml` file;
2. add a default value to `src/configs/default.yaml`;
3. load and validate the parameter in the corresponding configuration logic in `config.py`;
4. make the parameter available through the configuration object used by the modules;
5. document the parameter in the appropriate user documentation.

Hard-coded values should be avoided when the value may vary between scenarios, environments, or simulation modes.

Configuration names should be descriptive, consistent with the existing YAML structure, and grouped under the appropriate section.

Example:

```yaml
blensor:
  drone_altitude: 10.0
```

The source code should access the value through the configuration object instead of defining it locally:

```python
drone_altitude = c.blensor.drone_altitude
```

## 2. Adding New Modules

New functionality must be added to the appropriate directory under:

```text
src/modules/
```

The module location should reflect its responsibility. Existing categories include:

```text
src/modules/
├── mobility/
├── rt/
├── blensor/
├── postprocessing/
└── data_processing/
```

Avoid creating a new top-level module directory when the functionality clearly belongs to an existing category.

When adding a new module:

1. place the implementation in the appropriate module directory;
2. expose a clear entry function or class;
3. integrate the module into the main pipeline in `raymobtime()`;
4. define its configuration parameters in the YAML files;
5. document its required inputs and generated outputs;
6. update the relevant documentation files:

   * `doc/1-Setup.md`;
   * `doc/2-BaseCreation.md`;
   * `doc/3-DatasetCreation.md`;
7. add validation and error handling;
8. test the module independently and as part of the complete pipeline.

## 3. Pipeline Integration

All modules must follow the Raymobtime input/output organization.

Scenario inputs should be read from:

```text
data/<scenario_name>/
```

Base scenario resources should normally be stored under:

```text
data/<scenario_name>/base/
```

Generated data should be written under:

```text
data/<scenario_name>/outputs/
```

Modules should not write files to arbitrary project directories. Output locations must be defined through the configuration system or derived from the selected scenario path.

A module should clearly define:

* its required input files;
* its configuration dependencies;
* its execution conditions;
* its generated output files;
* its expected directory structure;
* its failure behavior.

The main `raymobtime()` pipeline should determine whether a module is executed according to the enabled features and available configuration.

## 4. Input and Output Consistency

Each module should preserve the expected data flow between simulation stages.

Before implementing a new output format, verify whether the data will be consumed by another module. Changes to file names, directory structures, column names, JSON keys, or array dimensions may require updates in multiple parts of the pipeline.

The following should be documented whenever relevant:

* file format;
* data types;
* array dimensions;
* coordinate system;
* units;
* naming convention;
* required metadata;
* relationship with other generated files.

Do not silently overwrite unrelated outputs. When multiple simulation modes generate similar resources, use separate directories or descriptive file names.

## 5. Documentation

All public functions, methods, and classes should contain docstrings.

Docstrings should describe:

* the purpose of the function or class;
* parameters and their expected types;
* return values;
* generated files or side effects;
* raised exceptions, when relevant.

Example:

```python
def generate_routes(
    output_file: str,
    initial_time: int,
    end_time: int,
) -> None:
    """
    Generate a SUMO route file for the selected simulation interval.

    Args:
        output_file: Path of the route file to be generated.
        initial_time: Initial simulation time in seconds.
        end_time: Final simulation time in seconds.

    Returns:
        None. The generated route data is written to ``output_file``.

    Raises:
        ValueError: If ``end_time`` is smaller than ``initial_time``.
    """
```

Comments should explain decisions, assumptions, or non-obvious behavior. Avoid comments that only repeat what the code already expresses.

When a feature changes the installation process, base-scenario preparation, or dataset-generation procedure, update the corresponding Markdown documentation in the same contribution.

## 6. Logging

Use the Python `logging` module instead of direct `print()` calls for runtime messages.

Example:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Starting Wireless InSite simulation")
logger.warning("No pedestrian objects were generated")
logger.error("Wireless InSite execution failed")
```

Recommended logging levels:

* `DEBUG`: detailed information used during development;
* `INFO`: normal pipeline progress;
* `WARNING`: unexpected situations that do not stop execution;
* `ERROR`: failures that prevent a stage from completing;
* `CRITICAL`: failures that prevent the complete pipeline from continuing.

Avoid logging large arrays, complete configuration objects, or repetitive messages inside high-frequency loops unless the logging level is `DEBUG`.

Error messages should include enough context to identify the scenario, module, run, or file that caused the problem.

## 7. Auxiliary Resources

Static auxiliary files should be stored under:

```text
assets/
```

Examples include:

* antenna codebooks;
* Wireless InSite object templates;
* documentation images;
* reusable configuration resources;
* static models;
* lookup tables.

Files that belong to a specific scenario should remain under:

```text
data/<scenario_name>/base/
```

Do not store generated outputs, temporary files, or scenario-specific simulation results in `assets/`.

## 8. Imports and Project Structure

Imports must be self-contained within the project package.

Prefer package-based imports:

```python
from src.modules.mobility.simulation import run_mobility
```

Avoid imports that depend on the current working directory, manual `sys.path` modifications, or absolute paths from a developer's machine.

Do not use patterns such as:

```python
import sys

sys.path.append("/home/user/raymobtime")
```

Scripts should work when Raymobtime is installed or executed through the project entry point, regardless of the directory from which the command is called.

Circular imports should be avoided. Shared utilities should be moved to an appropriate reusable module.

## 9. Dependency Management

New Python libraries must be added using `uv`.

For example:

```bash
uv add <package-name>
```

After adding or updating a dependency, verify that the following files are consistent:

```text
pyproject.toml
uv.lock
requirements.txt
```

If `requirements.txt` is maintained for compatibility, regenerate or update it according to the project workflow.

Do not manually install a dependency only inside the local virtual environment without registering it in the project dependency files.

Before introducing a new dependency, verify whether the required functionality can be implemented using an existing project dependency or the Python standard library.

Dependencies should be compatible with the Python version supported by Raymobtime.

## 10. Generated Data and Repository Hygiene

Generated simulation outputs must not be committed to the remote repository.

This includes:

* Wireless InSite simulation outputs;
* SUMO runtime outputs;
* rendered images;
* LiDAR point clouds;
* HDF5 datasets;
* temporary JSON files;
* generated CSV files;
* logs;
* cache directories;
* intermediate Blender files;
* large generated datasets.

Relevant paths and file patterns should be added to `.gitignore`.

Before committing, inspect the staged files:

```bash
git status
```

Large datasets should be stored in the designated external storage service, such as the project Nextcloud, instead of the Git repository.

Small base-scenario files that are intentionally used for testing may be included only when they are necessary, documented, and approved for repository storage.

## 11. Temporary Files

Temporary files should be created in a dedicated temporary directory or through Python utilities such as `tempfile`.

Temporary resources must be removed after execution, including when an exception occurs.

Example:

```python
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as temp_dir:
    config_path = Path(temp_dir) / "runtime_config.json"
```

Avoid leaving temporary configuration files, rendered resources, or simulator intermediate files in the repository root.

## 12. Error Handling

Modules should validate their inputs before starting expensive simulation stages.

Check, when applicable:

* whether required files exist;
* whether executable paths are valid;
* whether output directories can be created;
* whether configuration values are valid;
* whether required external software is available;
* whether array dimensions and file formats are compatible.

Raise descriptive exceptions instead of allowing obscure errors to occur later.

Example:

```python
if not network_file.exists():
    raise FileNotFoundError(
        f"SUMO network file was not found: {network_file}"
    )
```

Do not suppress exceptions without logging or handling them appropriately.

## 13. Naming and Code Style

Use descriptive names for functions, classes, variables, files, and configuration fields.

Recommended conventions:

* functions and variables: `snake_case`;
* classes: `PascalCase`;
* constants: `UPPER_CASE`;
* YAML fields: `snake_case`;
* modules and files: `snake_case.py`.

Avoid unclear abbreviations unless they are already established in the project, such as `tx`, `rx`, `bs`, `ue`, or `rt`.

Functions should have a single clear responsibility. Long functions should be divided into smaller helper functions when this improves readability, testability, or reuse.

## 14. Testing Before Submission

Before submitting a contribution:

1. create an issue at repository for discuss new ideas;
1. synchronize the environment with `uv sync`;
1. verify that the modified module runs independently;
1. execute the relevant Raymobtime pipeline stages;
1. confirm that existing features still work;
1. validate generated file paths and formats;
1. review logging messages;
1. update the documentation;
1. verify that generated outputs are not staged;
1. run formatting, linting, or tests when available;
1. inspect the final diff.

Useful commands include:

```bash
git status
git diff
```
A contribution should not be considered complete until the code, configuration, and documentation are consistent.

You may contact [our team](https://raymobtime.lasseufpa.org/team/) for additional information.
