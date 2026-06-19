import re
import os
import collections
import numpy as np

class ParsingError(Exception):
    pass

class P2mFileParser:
    """
    Base parser for Wireless InSite P2M files.

    This class provides common parsing logic for Wireless InSite ``.p2m`` files,
    including filename metadata extraction, header parsing, comment skipping,
    and receiver-by-receiver parsing. Specific P2M file types, such as DOA,
    paths, or CIR, should extend this class and implement ``_parse_receiver``.

    Attributes:
        filename: Path to the P2M file being parsed.
        file: Open file object used during parsing.
        data: Ordered dictionary containing parsed receiver data.
        project: Project name extracted from the filename.
        transmitter_set: Transmitter set index extracted from the filename.
        transmitter: Transmitter index extracted from the filename.
        receiver_set: Receiver set index extracted from the filename.
        n_receivers: Number of receivers declared in the P2M file header.
    """

    _filename_match_re = (r'^(?P<project>.*)' +
                          r'\.' +
                          r'(?P<type>((doa)|(paths)|(cir)))' +
                          r'\.' +
                          r't(?P<transmitter>\d+)'+
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
        """
        Return the parsed P2M data as a dictionary.

        Returns:
            Ordered dictionary containing the parsed data grouped by receiver.
        """
        return self.data

    def _parse_meta(self):
        """
        Parse metadata from the P2M filename.

        This method extracts the project name, transmitter index, transmitter set,
        and receiver set from the filename using the expected Wireless InSite P2M
        naming convention.

        Returns:
            None.

        Raises:
            AttributeError: If the filename does not match the expected pattern.
        """
        match = re.match(P2mFileParser._filename_match_re,
                         os.path.basename(self.filename))

        self.project = match.group('project')
        self.transmitter_set = int(match.group('transmitter_set'))
        self.transmitter = int(match.group('transmitter'))
        self.receiver_set = int(match.group('receiver_set'))

    def _parse(self):
        """
        Parse the full P2M file.

        This method opens the input file, parses filename metadata, reads the header,
        initializes the data dictionary, and delegates receiver-specific parsing to
        ``_parse_receiver``.

        Returns:
            None.

        Raises:
            FileNotFoundError: If the input file does not exist.
            ParsingError: If the file ends unexpectedly or is malformed.
        """
        with open(self.filename) as self.file:
            self._parse_meta()
            self._parse_header()
            self.data = collections.OrderedDict()
            for rec in range(self.n_receivers):
                self._parse_receiver()

    def _parse_header(self):
        """
        Parse the P2M file header.

        The header contains the number of receivers stored in the file.

        Returns:
            None.

        Raises:
            ValueError: If the receiver count cannot be converted to an integer.
            ParsingError: If the header line cannot be read.
        """
        line = self._get_next_line()
        self.n_receivers = int(line.strip())

    def _parse_receiver(self):
        raise NotImplementedError()

    def _get_next_line(self):
        """
        Return the next non-comment line from the P2M file.

        This method skips lines that start with ``#`` and returns the next valid
        content line. It should only be called when a new line is expected by the
        parser.

        Returns:
            The next non-comment line from the file.

        Raises:
            ParsingError: If the file is closed or the end of file is reached
                unexpectedly.
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

class P2MDoA(P2mFileParser):
    """
    Parser for Wireless InSite P2M direction-of-arrival files.

    This class parses ``.doa`` P2M files and stores direction information for
    each receiver and propagation path. Parsed data can be returned as a nested
    dictionary or converted into a NumPy array.

    Attributes:
        filename: Path to the DOA P2M file.
        data: Ordered dictionary containing direction vectors grouped by
            receiver and path.
    """

    _filename_match_re = (r'^(?P<project>.*)' +
                          r'\.' + 
                          r'doa' + 
                          r'\.' + 
                          r't(?P<transmitter>\d+)'+
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
        
    def get_data_ndarray(self):
        """
        Return the parsed direction-of-arrival data as a NumPy array.

        The returned array has shape ``(receiver, path, direction)``. Receivers with
        fewer paths than the maximum number of paths are padded with zeros.

        Returns:
            NumPy array containing direction data for all receivers and paths.
        """
        data_ndarray = np.zeros((self.n_receivers, self.biggest_n_paths(), 3))
        for rec_idx, path_dict in enumerate(self.data.values()):
            for path_idx, direction in enumerate(path_dict.values()):
                data_ndarray[rec_idx][path_idx][:] = direction
        return data_ndarray
    
    def biggest_n_paths(self):
        """
        Find the maximum number of paths among all receivers.

        Returns:
            Largest number of received paths found for any receiver.
        """
        biggest = -np.inf
        for receiver, receiver_v in self.data.items():
            n_paths = len(receiver_v)
            if n_paths > biggest:
                biggest = n_paths
        return biggest

    def _parse_receiver(self):
        """
        Parse direction-of-arrival data for one receiver.

        This method reads the receiver identifier and number of paths, then parses
        one direction vector for each path and stores the result in the internal
        ordered dictionary.

        Returns:
            None.

        Raises:
            ValueError: If receiver IDs, path IDs, or direction values cannot be
                converted to numeric types.
            ParsingError: If the file ends unexpectedly.
        """
        line = self._get_next_line()
        receiver, n_paths = [int(i) for i in line.split()]
        self.data[receiver] = collections.OrderedDict()
        for i in range(n_paths):
            line = self._get_next_line()
            sp_line = line.split()
            path = int(sp_line[0])
            direction = np.array([float(j) for j in sp_line[1:]])
            self.data[receiver][path] = direction

