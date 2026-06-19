import subprocess
import logging
import os

CALCPROP_BIN=r'"C:\Program Files\Remcom\Wireless InSite 3.2.0.3\bin\calc\calcprop"'

def add_opt(opt, formatter):
    if opt is not None:
        return formatter.format(opt=opt)
    else:
        return ''

class InSiteProject:
    """
    Wrapper for executing Wireless InSite projects from Python.

    This class stores the Wireless InSite project name and command-line binary
    used to execute ray-tracing simulations. It provides a method to run an X3D
    project file through the Wireless InSite batch interface.

    Attributes:
        _project_name: Wireless InSite project name used in the command-line call.
        _wibatch_bin: Path or command string for the Wireless InSite batch
            executable.
    """

    def __init__(self, project_name='model',
                 wibatch_bin=None):
        """InSite project
        :param calcprop_bin: the path to InSite's calcprop binary
        """
        self._project_name = project_name
        self._wibatch_bin = wibatch_bin


    def run_x3d(self, xml_path, output_dir):
        """
        Run a Wireless InSite X3D project using the batch executable.

        This method builds a command-line call using the configured Wireless InSite
        batch binary, output directory, X3D XML file path, and project name. The
        command is logged and then executed through ``subprocess.run``.

        Args:
            xml_path: Path to the X3D XML project file to be executed.
            output_dir: Directory where Wireless InSite should store the simulation
                results.

        Returns:
            None.

        Raises:
            subprocess.CalledProcessError: If the Wireless InSite command returns a
                non-zero exit status.
        """
        cmd = ''
        cmd += self._wibatch_bin
        cmd += add_opt(output_dir, ' -out {opt}')
        cmd += add_opt(xml_path, ' -f {opt}')
        cmd += add_opt(self._project_name, ' -p {opt}')
        logging.info('Running CMD: "{}"'.format(cmd))
        subprocess.run(cmd, shell=True, check=True)
