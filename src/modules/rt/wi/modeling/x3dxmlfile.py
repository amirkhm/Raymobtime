from xml.etree import ElementTree
from src.modules.rt.wi.modeling.errors import FormatError

class X3dXmlFile3_3:
    """
    XML handler for Wireless InSite 3.3 X3D files.

    This class loads an X3D XML file, updates vertex lists at selected XML
    locations, and writes the modified file back to disk. It also handles the
    namespace separator used in Wireless InSite 3.3 files by temporarily
    replacing ``::`` with ``__`` so that Python's XML parser can process the
    file correctly.

    Attributes:
        _file_name: Path to the loaded XML file.
        _et: Parsed ElementTree object representing the XML document.
    """

    def __init__(self, file_name):
        self._file_name = file_name
        string = open(file_name, 'r').read().replace('::','__')
        with open(file_name, "w") as text_file:
            text_file.write(string)
        self._load_et(file_name)

    def _load_et(self, file_name):
        self._et = ElementTree.parse(file_name)

    def add_vertice_list(self, vertice_list, xpath, clear=True):
        """
        Add a vertex list to a selected XML point-list element.

        This method finds a single XML element using the provided XPath and appends
        the vertices from ``vertice_list`` as ``ProjectedPoint`` entries. Each vertex
        is written as a Cartesian point with X, Y, and Z coordinates using the
        Wireless InSite 3.3 XML tag format.

        Args:
            vertice_list: Vertex list object containing ``vertice_array`` and
                ``float_format_string`` attributes.
            xpath: XPath expression used to select the target XML point-list element.
            clear: Whether to remove existing children from the selected XML element
                before adding the new vertices. Defaults to ``True``.

        Returns:
            None.

        Raises:
            FormatError: If the XPath does not select exactly one XML element.
            AttributeError: If ``vertice_list`` does not provide the expected
                attributes.
        """
        point_list = self._et.findall(xpath)
        if len(point_list) != 1:
            raise FormatError(
                'xpath is not selecting only one element. xpath: "{}" selected: "{}"'.format(xpath, point_list))
        point_list = point_list[0]
        if clear:
            point_list.clear()

        def add_vertice(vertice):
            def add_point(point, name, value):
                name_element = ElementTree.SubElement(point, name)
                double = ElementTree.SubElement(name_element, 'remcom__rxapi__Double')
                double.set('Value', vertice_list.float_format_string.format(value))

            projected_point = ElementTree.SubElement(point_list, 'ProjectedPoint')
            point = ElementTree.SubElement(projected_point, 'remcom__rxapi__CartesianPoint')

            for name, value in zip(('X', 'Y', 'Z'), vertice):
                add_point(point, name, value)

        for vertice in vertice_list.vertice_array:
            add_vertice(vertice)


    def write(self, file_name):
        self._et.write(file_name, short_empty_elements=False)
        string = open(file_name, 'r').read().replace('__','::')
        with open(file_name, "w") as text_file:
            text_file.write(string)
        

class X3dXmlFile:
    """
    XML handler for standard Wireless InSite X3D files.

    This class loads an X3D XML file, allows vertex lists to be inserted into
    selected XML point-list elements, and writes the modified XML structure back
    to disk.

    Attributes:
        _file_name: Path to the loaded XML file.
        _et: Parsed ElementTree object representing the XML document.
    """

    def __init__(self, file_name):
        self._file_name = file_name
        self._load_et(file_name)

    def _load_et(self, file_name):
        self._et = ElementTree.parse(file_name)

    def add_vertice_list(self, vertice_list, xpath, clear=True):
        point_list = self._et.findall(xpath)
        if len(point_list) != 1:
            raise FormatError(
                'xpath is not selecting only one element. xpath: "{}" selected: "{}"'.format(xpath, point_list))
        point_list = point_list[0]
        if clear:
            point_list.clear()

        def add_vertice(vertice):
            def add_point(point, name, value):
                name_element = ElementTree.SubElement(point, name)
                double = ElementTree.SubElement(name_element, 'Double')
                double.set('Value', vertice_list.float_format_string.format(value))

            projected_point = ElementTree.SubElement(point_list, 'ProjectedPoint')
            point = ElementTree.SubElement(projected_point, 'CartesianPoint')

            for name, value in zip(('X', 'Y', 'Z'), vertice):
                add_point(point, name, value)

        for vertice in vertice_list.vertice_array:
            add_vertice(vertice)

    def write(self, file_name):
        self._et.write(file_name, short_empty_elements=False)
