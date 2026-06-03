import numpy as np
import os.path
import logging
from termcolor import colored
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as db
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from src.modules.rt.wi.modeling.errors import FormatError

Base = declarative_base()

class Episode(Base):
    """
    SQLAlchemy model representing a simulation episode.

    An episode groups multiple simulation scenes and stores metadata related to
    the Wireless InSite project path, SUMO path, simulation start time, and
    sampling interval.

    Attributes:
        id: Primary key identifier of the episode.
        insite_pah: Path to the Wireless InSite data associated with the episode.
        sumo_path: Path to the SUMO data associated with the episode.
        simulation_time_begin: Initial simulation time for the episode.
        sampling_time: Sampling interval used between scenes.
    """
    __tablename__ = 'episodes'

    id = db.Column(db.Integer, primary_key=True, index=True)

    insite_pah = db.Column(db.String)
    sumo_path = db.Column(db.String)
    simulation_time_begin = db.Column(db.Integer)
    sampling_time = db.Column(db.Float)

    @property
    def number_of_scenes(self):
        """
        Return the number of scenes associated with this episode.

        Returns:
            Number of Scene objects linked to this episode.
        """
        return len(self.scenes)

class InsiteObject(Base):
    """
    SQLAlchemy model representing an object in a Wireless InSite scene.

    This model stores object geometry, position, dimensions, height, angle, and
    its relationship with a scene. Geometric arrays are stored as binary fields
    and converted to NumPy arrays through property getters and setters.

    Attributes:
        id: Primary key identifier of the object.
        name: Object name.
        height: Object height.
        angle: Object orientation angle.
        scene_id: Foreign key referencing the associated scene.
        scene: Scene object associated with this object.
    """
    __tablename__ = 'objects'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String)
    _dimension = db.Column(db.LargeBinary)
    _vertice_array = db.Column(db.LargeBinary)
    _position = db.Column(db.LargeBinary)

    height = db.Column(db.Float)
    angle = db.Column(db.Float)

    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'), index=True)
    scene = relationship("Scene", backref="objects")

    @property
    def dimension(self):
        """
        Return the object dimensions as a NumPy array.

        Returns:
            A NumPy array with shape ``(3,)`` containing the object dimensions.
        """
        return np.frombuffer(self._dimension, np.float64).reshape((3,))

    @dimension.setter
    def dimension(self, v):
        """
        Store the object dimensions as a binary NumPy array.

        Args:
            v: Array-like object containing exactly three dimension values.

        Raises:
            FormatError: If the provided value cannot be reshaped to ``(3,)``.
        """
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._dimension = v.tobytes()

    @property
    def position(self):
        """
        Return the object position as a NumPy array.

        Returns:
            A NumPy array with shape ``(3,)`` containing the object position.
        """
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        """
        Store the object position as a binary NumPy array.

        Args:
            v: Array-like object containing exactly three position values.

        Raises:
            FormatError: If the provided value cannot be reshaped to ``(3,)``.
        """
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def vertice_array(self):
        """
        Return the object vertices as a NumPy array.

        Returns:
            A NumPy array with shape ``(N, 3)`` containing the vertices of the object.
        """
        return np.frombuffer(self._vertice_array, np.float64).reshape((-1,3))

    @vertice_array.setter
    def vertice_array(self, v):
        """
        Store the object vertices as a binary NumPy array.

        Args:
            v: Array-like object containing object vertices with shape ``(N, 3)``.

        Raises:
            FormatError: If the provided value is not a two-dimensional array with
                three columns.
        """
        v = np.array(v, np.float64)
        if v.ndim != 2 or v.shape[1] != 3:
            raise FormatError()
        self._vertice_array = v.tobytes()

class InsiteReceiver(Base):
    """
    SQLAlchemy model representing a Wireless InSite receiver.

    A receiver stores aggregate ray-tracing information, its 3D position, and
    its relationship with the object to which it belongs. Receiver positions are
    stored as binary NumPy arrays and accessed through property methods.

    Attributes:
        id: Primary key identifier of the receiver.
        total_received_power: Total received power at the receiver.
        mean_time_of_arrival: Mean time of arrival of received rays.
        object_id: Foreign key referencing the associated object.
        objects: InsiteObject associated with this receiver.
    """
    __tablename__ = 'receivers'

    id = db.Column(db.Integer, primary_key=True, index=True)
    total_received_power = db.Column(db.Float)
    mean_time_of_arrival = db.Column(db.Float)
    _position = db.Column(db.LargeBinary)

    object_id = db.Column(db.Integer, db.ForeignKey('objects.id'), index=True)
    objects = relationship("InsiteObject", backref="receivers")

    @property
    def position(self):
        """
        Return the receiver position as a NumPy array.

        Returns:
            A NumPy array with shape ``(3,)`` containing the receiver position.
        """
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        """
        Store the receiver position as a binary NumPy array.

        Args:
            v: Array-like object containing exactly three position values.

        Raises:
            FormatError: If the provided value cannot be reshaped to ``(3,)``.
        """
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def number_of_rays(self):
        """
        Return the number of rays associated with this receiver.

        Returns:
            Number of Ray objects linked to this receiver.
        """
        return len(self.rays)

class InsiteTransmitter(Base):
    """
    SQLAlchemy model representing a Wireless InSite transmitter.

    A transmitter stores its 3D position and its relationship with the object to
    which it belongs. Transmitter positions are stored as binary NumPy arrays and
    accessed through property methods.

    Attributes:
        id: Primary key identifier of the transmitter.
        object_id: Foreign key referencing the associated object.
        objects: InsiteObject associated with this transmitter.
    """
    __tablename__ = 'transmitter'

    id = db.Column(db.Integer, primary_key=True, index=True)
    _position = db.Column(db.LargeBinary)

    object_id = db.Column(db.Integer, db.ForeignKey('objects.id'), index=True)
    objects = relationship("InsiteObject", backref="transmitter")

    @property
    def position(self):
        """
        Return the transmitter position as a NumPy array.

        Returns:
            A NumPy array with shape ``(3,)`` containing the transmitter position.
        """
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        """
        Store the transmitter position as a binary NumPy array.

        Args:
            v: Array-like object containing exactly three position values.

        Raises:
            FormatError: If the provided value cannot be reshaped to ``(3,)``.
        """
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def number_of_rays(self):
        """
        Return the number of rays associated with this transmitter.

        Returns:
            Number of Ray objects linked to this transmitter.

        Notes:
            This property assumes that a ``rays`` relationship exists for the
            transmitter. If such a relationship is not defined, accessing this
            property may raise an attribute error.
        """
        return len(self.rays)

class Ray(Base):
    """
    SQLAlchemy model representing a propagation ray.

    A ray stores angular, power, delay, phase, and interaction information
    extracted from Wireless InSite ray-tracing outputs. Each ray is associated
    with a receiver.

    Attributes:
        id: Primary key identifier of the ray.
        departure_elevation: Elevation angle of departure.
        departure_azimuth: Azimuth angle of departure.
        arrival_elevation: Elevation angle of arrival.
        arrival_azimuth: Azimuth angle of arrival.
        path_gain: Path gain of the ray.
        time_of_arrival: Time of arrival of the ray.
        interactions: String describing the ray interactions.
        phaseInDegrees: Ray phase in degrees.
        interactionsPositions: String containing interaction positions.
        receiver_id: Foreign key referencing the associated receiver.
        receiver: InsiteReceiver associated with this ray.
    """
    __tablename__ = 'rays'

    id = db.Column(db.Integer, primary_key=True, index=True)
    departure_elevation = db.Column(db.Float)
    departure_azimuth = db.Column(db.Float)
    arrival_elevation = db.Column(db.Float)
    arrival_azimuth = db.Column(db.Float)
    path_gain = db.Column(db.Float)
    time_of_arrival = db.Column(db.Float)
    interactions = db.Column(db.String)
    phaseInDegrees = db.Column(db.Float)
    interactionsPositions = db.Column(db.String)

    receiver_id = db.Column(db.Integer, db.ForeignKey('receivers.id'),
                            index=True)
    receiver = relationship("InsiteReceiver", backref="rays")

    @property
    def is_los(self):
        """
        Check whether the ray is line-of-sight.

        Returns:
            ``True`` if the ray interaction string indicates a direct path,
            otherwise ``False``.
        """
        return len(self.interactions.split('-')) == 2

class Scene(Base):
    """
    SQLAlchemy model representing a simulation scene.

    A scene belongs to one episode and contains multiple Wireless InSite objects.
    It stores the study area geometry as a binary NumPy array and provides helper
    properties for counting receivers and mobile objects.

    Attributes:
        id: Primary key identifier of the scene.
        episode_id: Foreign key referencing the associated episode.
        episode: Episode object associated with this scene.
    """
    __tablename__ = 'scenes'

    """- map between transmitters and mobile objects
            - map between receivers and mobile objects"""

    id = db.Column(db.Integer, primary_key=True, index=True)
    _study_area = db.Column(db.LargeBinary)

    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'), index=True)
    episode = relationship("Episode", backref="scenes")

    @property
    def study_area(self):
        """
        Return the scene study area bounds as a NumPy array.

        Returns:
            A NumPy array with shape ``(2, 3)`` representing the study area bounds.
        """
        return np.frombuffer(self._study_area, np.float64).reshape((2, 3))

    @study_area.setter
    def study_area(self, v):
        """
        Store the scene study area bounds as a binary NumPy array.

        Args:
            v: Array-like object containing study area bounds with shape ``(2, 3)``.

        Raises:
            FormatError: If the provided value cannot be reshaped to ``(2, 3)``.
        """
        v = np.array(v, np.float64)
        if v.shape != (2, 3):
            raise FormatError()
        self._study_area = v.tobytes()

    @property
    def number_of_transmitters(self):
        """
        Return the number of transmitters in the scene.

        Raises:
            NotImplementedError: This property is currently not implemented.
        """
        raise NotImplementedError()

    @property
    def number_of_receivers(self):
        """
        Return the number of receivers in the scene.

        This property counts all receivers associated with all objects in the scene.

        Returns:
            Total number of receivers linked to the scene objects.
        """
        n_rec = 0
        for obj in self.objects:
            n_rec += len(obj.receivers)
        return n_rec

    @property
    def number_of_mobile_objects(self):
        """
        Return the number of mobile objects in the scene.

        Returns:
            Number of objects associated with this scene.
        """
        return len(self.objects)
    
def create_database(dataBaseFileName='episodedata.db'):
    
    if os.path.isfile(dataBaseFileName):
        os.remove(dataBaseFileName)
        logging.warning(
            '\033[31m'
            f'Removed old database:\n'
            '\033[90m'
            f'   {dataBaseFileName}'
            '\033[0m')
    else:
        logging.info(
            '\033[92m'
            f'Created a empty database:\n'
            '\033[90m'
            f'   {dataBaseFileName}'
            '\033[0m')
    engine = create_engine('sqlite:///' + dataBaseFileName)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    return Session()

def open_database(dataBaseFileName='episodedata.db'):
    
    if os.path.isfile(dataBaseFileName):
        print(f'Found database file: {dataBaseFileName}')
    else:
        print(colored(f'File: {dataBaseFileName} no found', 'red'))
        exit(-1)
    print('##############################')
    engine = create_engine('sqlite:///' + dataBaseFileName)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    return Session()

