import numpy as np

from src.modules.rt.wi.modeling.basecontainerobject import BaseContainerObject
from src.modules.rt.wi.modeling.face import Face
from src.modules.rt.wi.modeling.utils import match_or_error

try:
    from shapely import geometry
except ImportError:
    geometry = None

class SubStructure(BaseContainerObject):
    """
    Container representing a Wireless InSite substructure.

    A substructure is composed of one or more faces and can be parsed from or
    serialized to a Wireless InSite object file. This class also provides helper
    methods to retrieve all vertices, generate a 2D polygon projection, and
    rotate all faces that belong to the substructure.

    Attributes:
        name: Substructure name.
        face_list: List of Face objects contained in the substructure.
    """

    def __init__(self, **kargs):
        BaseContainerObject.__init__(self, Face, **kargs)
        self._begin_re = r'^\s*begin_<sub_structure>\s+(?P<sstname>.*)\s*$'
        self._end_re = r'^\s*end_<sub_structure>\s*$'

    @property
    def face_list(self):
        return self._child_list

    def add_faces(self, faces):
        self.append(faces)

    def as_polygon(self, axis=(0, 1)):
        """
        Convert the substructure vertices into a 2D convex polygon.

        This function projects the substructure vertices onto the selected coordinate
        axes and builds a convex hull using Shapely.

        Args:
            axis: Pair of coordinate axes used for the 2D projection. Defaults to
                ``(0, 1)``, corresponding to the x-y plane.

        Returns:
            A Shapely polygon representing the convex hull of the projected vertices.

        Raises:
            NotImplementedError: If the Shapely module is not available.
        """
        if geometry is None:
            raise NotImplementedError('shapely module was not found')
        return geometry.asMultiPoint(
            self.as_vertice_array()[:,axis]
        ).convex_hull

    def as_vertice_array(self):
        """
        Return all vertices from all faces as a single NumPy array.

        This function concatenates the vertex arrays of all faces contained in the
        substructure.

        Returns:
            A NumPy array containing all vertices from the substructure faces. If no
            face contains vertices, returns ``None``.
        """
        vertice_array = None
        for face in self.face_list:
            if face.vertice_array is not None:
                if vertice_array is None:
                    vertice_array = np.array(face.vertice_array)
                else:
                    vertice_array = np.concatenate((vertice_array, face.vertice_array))
        return vertice_array

    def rotate(self, angle):
        for f in self.face_list:
            f.rotate(angle)

    @property
    def _header(self):
        header_str = ''
        header_str += 'begin_<sub_structure> {}\n'.format(self.name)
        return header_str

    @property
    def _tail(self):
        tail_str = ''
        tail_str += 'end_<sub_structure>\n'
        return tail_str

    def _parse_head(self, infile):
        match = match_or_error(self._begin_re, infile)
        self.name = match.group('sstname')

    def from_file(infile):
        inst = SubStructure()
        BaseContainerObject.from_file(inst, infile)
        return inst