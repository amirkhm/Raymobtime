from src.modules.rt.wi.modeling.basecontainerobject import BaseContainerObject
from src.modules.rt.wi.modeling.utils import match_or_error
from src.modules.rt.wi.modeling.verticelist import VerticeList

class Location(VerticeList, BaseContainerObject):
    """
    Container representing a Wireless InSite location block.

    A location stores a list of vertices and provides parsing and serialization
    support for ``begin_<location>`` blocks in Wireless InSite transmitter or
    receiver point files.

    Attributes:
        vertice_float_precision: Number of decimal places used when serializing
            vertex coordinates.
    """

    def __init__(self):
        VerticeList.__init__(self)
        BaseContainerObject.__init__(self, None)
        self._end_header_re = VerticeList._begin_re
        self._end_re = r'^\s*end_<location>\s*$'
        self.vertice_float_precision = 15

    @property
    def _content(self):
        return VerticeList.serialize(self)

    @property
    def _tail(self):
        return 'end_<location>\n'

    def from_file(infile):
        inst = Location()
        BaseContainerObject.from_file(inst, infile)
        return inst

    def _parse_content(self, infile):
        VerticeList.from_file(infile, self)

    def serialize(self):
        return BaseContainerObject.serialize(self)


class TxRx(BaseContainerObject):
    """
    Container representing a Wireless InSite transmitter or receiver points block.

    This class stores one or more ``Location`` objects and provides parsing and
    serialization support for ``begin_<points>`` blocks, which are commonly used
    to define transmitter or receiver positions in Wireless InSite files.

    Attributes:
        name: Name of the points block.
        location_list: List of Location objects contained in this block.
    """

    def __init__(self, name=''):
        BaseContainerObject.__init__(self, Location, name=name)
        self.__begin_re = r'^\s*begin_<points>\s+(?P<name>.*)\s*$'
        self._end_header_re = r'^\s*begin_<location>\s*$'
        # the tail starts if the "content" is not a location
        self._begin_tail_re = r'^(?!begin_<location>).*$'
        self._end_re = r'^\s*end_<points>\s*$'

    def from_file(infile):
        inst = TxRx()
        BaseContainerObject.from_file(inst, infile)
        return inst

    @property
    def location_list(self):
        return self._child_list

    def _parse_head(self, infile):
        # read the name (could read here any parameter of interest)
        match = match_or_error(self.__begin_re, infile)
        self.name = match.group('name')
        # read header that will not be parsed, but cached to output
        BaseContainerObject._parse_head(self, infile)

    @property
    def _header(self):
        # insert the name (parsed parameter)
        header_str = 'begin_<points> {}\n'.format(self.name)
        # insert string read in the header but not parsed
        header_str += BaseContainerObject._header.fget(self)
        return header_str


class TxRxFile(BaseContainerObject):
    """
    Container representing a complete Wireless InSite transmitter/receiver file.

    This class stores one or more ``TxRx`` point blocks and provides parsing and
    serialization support for files that define transmitter or receiver
    locations.

    Attributes:
        name: Optional file/container name.
    """

    def __init__(self, name=''):
        BaseContainerObject.__init__(self, TxRx, name=name)
        self._end_header_re = r'^\s*begin_<points>.*$'
        self._end_re = r'^$'

    @property
    def _tail(self):
        return ''

    def from_file(infile):
        inst = TxRxFile()
        BaseContainerObject.from_file(inst, infile)
        return inst
