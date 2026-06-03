import collections
import numpy as np
import re
import os

class ParsingError(Exception):
    pass

class P2mFileParser:
    """
    Base parser for Wireless InSite P2M files.

    This class provides common parsing logic for P2M files, including filename
    metadata extraction, header parsing, comment skipping, and receiver-specific
    parsing. Subclasses must implement ``_parse_receiver`` according to the
    specific P2M file type.

    Supported file types in the filename pattern include ``doa``, ``paths``,
    and ``positions``.

    Attributes:
        filename: Path to the P2M file being parsed.
        file: Open file object used during parsing.
        data: Ordered dictionary containing parsed data.
        project: Project name extracted from the filename.
        transmitter_set: Transmitter set index extracted from the filename.
        transmitter: Transmitter index extracted from the filename.
        receiver_set: Receiver set index extracted from the filename.
        n_receivers: Number of receivers declared in the file header.
    """
    _filename_match_re = (r'^(?P<project>.*)' +
                          r'\.' +
                          r'(?P<type>((doa)|(paths)|(positions)))' +
                          r'\.' +
                          r't(?P<transmitter>\d+)' +
                          r'_' +
                          r'(?P<transmitter_set>\d+)' +
                          r'\.' +
                          r'r(?P<receiver_set>\d+)' +
                          r'\.' +
                          r'p2m$')

    def __init__(self, filename):
        self.filename = filename
        self.file = None
        self._parse()

    def get_data_dict(self):
        return self.data

    def _parse_meta(self):
        match = re.match(P2mFileParser._filename_match_re,
                         os.path.basename(self.filename))
        self.project = match.group('project')
        self.transmitter_set = int(match.group('transmitter_set'))
        self.transmitter = int(match.group('transmitter'))
        self.receiver_set = int(match.group('receiver_set'))

    def _parse(self):
        with open(self.filename) as self.file:
            self._parse_meta()
            self._parse_header()
            self.data = collections.OrderedDict()
            for rec in range(self.n_receivers):
                self._parse_receiver()

    def _parse_header(self):
        """read the first line of the file, indicating the number of receivers"""
        line = self._get_next_line()
        self.n_receivers = int(line.strip())

    def _parse_receiver(self):
        raise NotImplementedError()

    def _get_next_line(self):
        """Get the next uncommedted line of the file

        Call this only if a new line is expected
        """
        if self.file is None:
            raise ParsingError('File is closed')
        while True:
            next_line = self.file.readline()
            if next_line == '':
                raise ParsingError('Unexpected end of file')
            if re.search(r'^\s*#', next_line, re.DOTALL):
                continue
            else:
                return next_line


class P2mCir(P2mFileParser):
    """
    Parser for Wireless InSite P2M position files.

    Despite the class name, this implementation parses position-like P2M data.
    For each parsed block, it reads the simulation time, the number of vehicles,
    and, for each vehicle, its name, position, velocity, and acceleration.

    Attributes:
        data: Ordered dictionary containing parsed vehicle position information.
            The main entry is stored under the ``"positions"`` key.
    """

    def _parse_receiver(self):
        """Get receiver and number of paths (pair Tx-Rx)"""
        line = self._get_next_line()
        time = int(line)
        line = self._get_next_line()
        n_veh = int(line)
        print('time = ', time)  # TODO take out
        print('print n_veh = ', n_veh)
        self.data["positions"] = collections.OrderedDict()
        self.data["positions"]["time"] = time
        if n_veh == 0:
            self.data["positions"] = None
            return
        """Read: phase, arrival_time and power of a ray"""
        for veh in range(n_veh):
            self.data["positions"][veh] = collections.OrderedDict()
            line = self._get_next_line()
            veh_name = str(line)
            self.data["positions"][veh]['name'] = veh_name
            line = self._get_next_line()
            x, y, z, vel, acel = [float(i) for i in line.split()]
            self.data["positions"][veh]['x'] = x
            self.data["positions"][veh]['y'] = y
            self.data["positions"][veh]['z'] = z
            self.data["positions"][veh]['vel'] = vel
            self.data["positions"][veh]['acel'] = acel

    def get_phase_ndarray(self, antenna_number):
        if self.data[antenna_number] is None:
            return None
        data_ndarray = np.zeros((self.data[antenna_number]['paths_number'],))
        for paths in range(self.data[antenna_number]['paths_number']):
            data_ndarray[paths] = self.data[antenna_number][paths + 1]['phase']
        return data_ndarray
