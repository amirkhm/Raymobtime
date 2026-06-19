import re
from src.modules.rt.wi.modeling.errors import FormatError
from src.modules.rt.wi.modeling.utils import match_or_error, look_next_line

MAX_LEN_NAME = 71


class BaseObject():
    """
    Base class for Wireless InSite modeling objects.

    This class stores common metadata shared by modeling entities, such as the
    object name, material identifier, and dimensions. It also validates the
    object name length according to the Wireless InSite file format limitation.

    Attributes:
        material: Material identifier associated with the object.
        name: Object name.
        dimensions: Object dimensions, initialized as ``None``.
    """
    def __init__(self, name='', material=0):
        self.material = material
        self.name = name
        self.dimensions = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if len(name) > MAX_LEN_NAME:
            raise FormatError(
                'Max len for name is {}'.format(MAX_LEN_NAME))
        else:
            self._name = name


class BaseContainerObject(BaseObject):
    """
    Base class for Wireless InSite container objects.

    A container object stores and manages a list of child entities of a specific
    type. It provides common functionality for parsing file sections, appending
    children, translating child objects, serializing the container, writing it to
    disk, and iterating over its contents.

    Attributes:
        _child_list: List of child entities stored in the container.
        _child_type: Expected class type for child entities.
        _begin_re: Regular expression that marks the beginning of the entity.
        _end_header_re: Regular expression that marks the end of the header.
        _begin_tail_re: Regular expression that marks the beginning of the tail.
        _end_re: Regular expression that marks the end of the entity.
        _header_str: Serialized header string.
        _tail_str: Serialized tail string.
    """

    def __init__(self, child_type, **kargs):
        BaseObject.__init__(self, **kargs)
        # list of child entities
        self._child_list = []
        # type of child entities
        self._child_type = child_type
        # define the first line of the entity (assumes the header has only one line)
        self._begin_re = None
        # define the end of the entity header used only if _begin_re is None
        self._end_header_re = None
        # define when start parsing the entity tail
        self._begin_tail_re = None
        # define the end of entity, it None the entity ends in the end of the file
        # (if _begin_tail_re is not defined it is required, the _tail must be implemented)
        self._end_re = None
        # default header and tail strings
        self._header_str = None
        self._tail_str = None

    @property
    def _header(self):
        return self._header_str

    @property
    def _tail(self):
        return self._tail_str

    @property
    def _content(self):
        content_str = ''
        for child in self._child_list:
            content_str += child.serialize()
        return content_str

    def append(self, children):
        """
        Append one or more child objects to the container.

        This method verifies that every appended object matches the expected child
        type before inserting it into the internal child list.

        Args:
            children: A single child object or a list of child objects to append.

        Raises:
            NotImplementedError: If the container does not define a child type.
            FormatError: If any child object does not match the expected child type.
        """
        # only allow insertion of typed elements
        if self._child_type is None:
            raise NotImplementedError()
        if not isinstance(children, list):
            children = [children]

        def _check_and_add_child(child):
            if (not isinstance(child, self._child_type)):
                raise FormatError(
                    'Object is not a "{}" "{}"'.format(
                        self._child_type, child))
            self._child_list.append(child)
        for child in children:
            _check_and_add_child(child)

    def clear(self):
        self._child_list = []

    def translate(self, v):
        for child in self._child_list:
            child.translate(v)

    def serialize(self):
        mstr = ''
        mstr += self._header
        mstr += self._content
        mstr += self._tail
        return mstr

    def write(self, filename):
        with open(filename, 'w', newline='\r\n') as dst_file:
            dst_file.write(self.serialize())

    def _parse_head(self, infile):
        """
        Parse the header section of a container entity.

        If ``_begin_re`` is defined, the first line must match it. Otherwise, the
        method reads the input file until ``_end_header_re`` is found and stores the
        consumed lines as the header string.

        Args:
            infile: Open input file object positioned at the beginning of the entity.

        Raises:
            FormatError: If the expected header pattern cannot be found.
            NotImplementedError: If neither ``_begin_re`` nor ``_end_header_re`` is
                defined.
        """
        self._header_str = ''
        # if _begin_re is defined it must match the first line and the processing ends
        #print(self._begin_re)
        if self._begin_re is not None:
            match_or_error(self._begin_re, infile)
        # if _begin_re is not defined read until _end_header_re
        elif self._end_header_re is not None:
            while True:
                line = look_next_line(infile)
                if line == '':
                    raise FormatError(
                        'Could not find "{}"'.format(self._end_header_re)
                    )
                if re.match(self._end_header_re, line):
                    break
                self._header_str += line
                # consumes the line
                infile.readline()

        else:
            raise NotImplementedError()

    def _parse_tail(self, infile):
        """
        Parse the tail section of a container entity.

        This method reads lines from the input file until ``_end_re`` is matched. If
        ``_end_re`` is ``None``, the file is read until the end.

        Args:
            infile: Open input file object positioned at the beginning of the tail.

        Raises:
            FormatError: If ``_end_re`` is defined but not found before the end of
                the file.
        """
        self._tail_str = ''
        while True:
            line = infile.readline()
            self._tail_str += line
            if line == '':
                # if in end of file is reached and _end_re was not found
                if self._end_re is not None:
                    raise FormatError(
                        'Could not find "{}"'.format(self._end_re)
                    )
                # if _end_re is None the procesing ends
                else:
                    break
            # if _end_re is defined, search for it
            if self._end_re is not None:
                if re.match(self._end_re, line):
                    break

    def _parse_content(self, infile,mimo_id = -1):
        if mimo_id == -1:
            child = self._child_type.from_file(infile)
        else:
            child = self._child_type.from_file(infile, mimo_id)
        self.append(child)

    def __getitem__(self, key):
        for child in self._child_list:
            if child.name == key:
                return child
        raise KeyError()

    def __iter__(self):
        return iter(self._child_list)

    def keys(self):
        keys = []
        for child in self._child_list:
            keys.append(child.name)
        return keys

    def from_file(self, infile, MIMO=False):
        """
        Parse a container entity from an input file.

        This method parses the container header, then repeatedly parses child
        entities until the beginning of the tail or the end of the entity is found.
        When MIMO mode is enabled, a sequential MIMO identifier is passed to each
        parsed child.

        Args:
            infile: Open input file object positioned at the beginning of the
                container entity.
            MIMO: Whether to parse child entities with sequential MIMO identifiers.
                Defaults to ``False``.

        Returns:
            None.

        Raises:
            FormatError: If the entity format does not match the expected patterns.
        """
        # consumes the entity header
    
        self._parse_head(infile)
        MIMO = MIMO
        mimo_id = -1
        while True:
            line = look_next_line(infile)
            # are we searching for the beginning of the tail
            if self._begin_tail_re is not None:
                if re.match(self._begin_tail_re, line):
                    self._parse_tail(infile)
                    break
            # if not we have to search for the end of the entity
            elif self._end_re is not None:
                if re.match(self._end_re, line):
                    infile.readline()
                    break
            # if it is not the start of the tail nor the end of the entity,
            # it is a child entity
            if MIMO:
                mimo_id += 1
                self._parse_content(infile, mimo_id=mimo_id)
            else:
                self._parse_content(infile)