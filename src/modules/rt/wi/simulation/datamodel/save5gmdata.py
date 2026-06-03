import numpy as np
import os.path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as db
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class FormatError(Exception):
    pass

class Episode(Base):
    """
    SQLAlchemy model representing a simulation episode.

    An episode groups multiple scenes and stores metadata related to the
    Wireless InSite path, SUMO path, simulation start time, and sampling time.

    Attributes:
        id: Primary key identifier of the episode.
        insite_pah: Path to the Wireless InSite data associated with the episode.
        sumo_path: Path to the SUMO data associated with the episode.
        simulation_time_begin: Initial simulation time of the episode.
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
        return len(self.scenes)


class InsiteObject(Base):
    """
    SQLAlchemy model representing an object in a Wireless InSite scene.

    This model stores object geometry, position, dimensions, and its relationship
    with a scene. Geometric arrays are stored as binary fields and converted to
    NumPy arrays through property getters and setters.

    Attributes:
        id: Primary key identifier of the object.
        name: Object name.
        scene_id: Foreign key referencing the associated scene.
        scene: Scene object associated with this object.
    """
    __tablename__ = 'objects'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String)
    _dimension = db.Column(db.LargeBinary)
    _vertice_array = db.Column(db.LargeBinary)
    _position = db.Column(db.LargeBinary)

    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'), index=True)
    scene = relationship("Scene", backref="objects")

    @property
    def dimension(self):
        return np.frombuffer(self._dimension, np.float64).reshape((3,))

    @dimension.setter
    def dimension(self, v):
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._dimension = v.tobytes()

    @property
    def position(self):
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def vertice_array(self):
        return np.frombuffer(self._vertice_array, np.float64).reshape((-1,3))

    @vertice_array.setter
    def vertice_array(self, v):
        v = np.array(v, np.float64)
        if v.ndim != 2 or v.shape[1] != 3:
            raise FormatError()
        self._vertice_array = v.tobytes()


class InsiteReceiver(Base):
    """
    SQLAlchemy model representing a Wireless InSite receiver.

    A receiver stores aggregate ray-tracing information, its 3D position, and
    its relationship with the object to which it belongs.

    Attributes:
        id: Primary key identifier of the receiver.
        total_received_power: Total received power at the receiver.
        mean_time_of_arrival: Mean time of arrival of received rays.
        object_id: Foreign key referencing the associated object.
        episode: InsiteObject associated with this receiver.
    """
    __tablename__ = 'receivers'

    id = db.Column(db.Integer, primary_key=True, index=True)
    total_received_power = db.Column(db.Float)
    mean_time_of_arrival = db.Column(db.Float)
    _position = db.Column(db.LargeBinary)

    object_id = db.Column(db.Integer, db.ForeignKey('objects.id'), index=True)
    episode = relationship("InsiteObject", backref="receivers")

    @property
    def position(self):
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def number_of_rays(self):
        return len(self.rays)


class Ray(Base):
    """
    SQLAlchemy model representing a propagation ray.

    A ray stores angular, temporal, power, phase, and interaction information
    extracted from Wireless InSite ray-tracing outputs. Each ray is associated
    with one receiver.

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
        interactionsPositions: String containing ray interaction positions.
        receiver_id: Foreign key referencing the associated receiver.
        episode: InsiteReceiver associated with this ray.
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
    episode = relationship("InsiteReceiver", backref="rays")

    @property
    def is_los(self):
        return len(self.interactions.split('-')) == 2


class Scene(Base):
    """
    SQLAlchemy model representing a simulation scene.

    A scene belongs to one episode and contains multiple Wireless InSite objects.
    It stores the study area geometry as a binary NumPy array and provides
    helper properties for counting receivers and mobile objects.

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
        return np.frombuffer(self._study_area, np.float64).reshape((2, 3))

    @study_area.setter
    def study_area(self, v):
        v = np.array(v, np.float64)
        if v.shape != (2, 3):
            raise FormatError()
        self._study_area = v.tobytes()

    @property
    def number_of_transmitters(self):
        raise NotImplementedError()

    @property
    def number_of_receivers(self):
        n_rec = 0
        for obj in self.objects:
            n_rec += len(obj.receivers)
        return n_rec

    @property
    def number_of_mobile_objects(self):
        return len(self.objects)

dataBaseFileName = 'episodedata.db'
print('########## Important ##########')
print('Will try to open database in file (should be in your current folder): ', dataBaseFileName)
if os.path.isfile(dataBaseFileName):
    print('Successfully opened ', dataBaseFileName)
else:
    print('ERROR: Could not find ', dataBaseFileName, ' I then created an empty database!')
print('##############################')
engine = create_engine('sqlite:///' + dataBaseFileName)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)

