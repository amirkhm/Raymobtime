import collections
import numpy as np

from src.modules.rt.wi.parsing.p2mdoa import P2mFileParser

class P2mCir(P2mFileParser):
    """
    Parser for Wireless InSite P2M CIR files.

    This class extends ``P2mFileParser`` to parse channel impulse response
    information from Wireless InSite ``.cir`` P2M files. For each receiver, it
    stores the number of paths and, for each ray, the phase, arrival time, and
    received power.

    Attributes:
        data: Parsed CIR data organized by receiver and ray index.
    """

    def _parse_receiver(self):
        """
        Parse CIR information for one receiver.

        This method reads the receiver identifier and the number of propagation
        paths associated with the Tx-Rx pair. If no paths are available, the receiver
        entry is set to ``None``. Otherwise, the method reads each ray entry and
        stores its phase, arrival time, and received power.

        Returns:
            None. Parsed data is stored internally in ``self.data``.

        Raises:
            ValueError: If receiver, path count, or ray values cannot be converted
                to the expected numeric types.
            IndexError: If a CIR data line does not contain the expected number of
                fields.
        """
        line = self._get_next_line()
        receiver, n_paths = [int(i) for i in line.split()]
        self.data[receiver] = collections.OrderedDict()
        self.data[receiver]['paths_number'] = n_paths
        if n_paths == 0:
            self.data[receiver] = None
            return
        """Read: phase, arrival_time and power of a ray"""
        for rays in range(n_paths):
            line = self._get_next_line()
            ray_n, phase, arrival_time, srcvdpower = [float(i) for i in line.split()]
            self.data[receiver][ray_n] = collections.OrderedDict()
            self.data[receiver][ray_n]['ray_n'] = ray_n
            self.data[receiver][ray_n]['phase'] = phase
            self.data[receiver][ray_n]['arrival_time'] = arrival_time
            self.data[receiver][ray_n]['srcvdpower'] = srcvdpower
            
    def get_phase_ndarray(self, antenna_number):
        """
        Return the ray phases for a receiver as a NumPy array.

        The receiver index follows the Wireless InSite convention and starts at 1,
        not 0. If the selected receiver has no valid paths, the function returns
        ``None``.

        Args:
            antenna_number: Receiver index whose ray phases should be extracted.
                The index starts at 1.

        Returns:
            A one-dimensional NumPy array containing the phase of each ray in
            degrees, or ``None`` if the receiver has no paths.

        Raises:
            KeyError: If the requested receiver index is not available in the parsed
                data.
        """
        if self.data[antenna_number] is None:
            return None
        data_ndarray = np.zeros((self.data[antenna_number]['paths_number'],))
        for paths in range(self.data[antenna_number]['paths_number']):
            data_ndarray[paths] = self.data[antenna_number][paths+1]['phase']
        return data_ndarray
        
