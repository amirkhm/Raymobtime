from sqlalchemy import create_engine, Column, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os.path
from termcolor import colored

Base = declarative_base()

class Receiver(Base):
    """
    SQLAlchemy model representing a receiver in a ray-tracing episode.

    Each receiver stores aggregated propagation information, such as total
    received power, mean time of arrival, and the number of rays associated
    with it. The receiver is linked to its propagation rays through a one-to-many
    relationship.

    Attributes:
        id: Primary key identifier of the receiver.
        total_received_power: Total received power associated with the receiver.
        mean_time_of_arrival: Mean time of arrival of all rays reaching the receiver.
        total_rays: Total number of rays associated with the receiver.
        rays: List of Ray objects associated with this receiver.
    """
    __tablename__ = 'receivers'
    id = Column(Integer, primary_key=True)
    total_received_power = Column(Float)
    mean_time_of_arrival = Column(Float)
    total_rays = Column(Integer)
    rays = relationship("Ray", back_populates="receiver")

class Ray(Base):
    """
    SQLAlchemy model representing a propagation ray.

    Each ray stores angular, temporal, power, phase, and interaction information
    extracted from the ray-tracing output. A ray is associated with one receiver
    through a foreign key relationship.

    Attributes:
        id: Primary key identifier of the ray.
        departure_elevation: Elevation angle of departure.
        departure_azimuth: Azimuth angle of departure.
        arrival_elevation: Elevation angle of arrival.
        arrival_azimuth: Azimuth angle of arrival.
        path_gain: Path gain associated with the ray.
        time_of_arrival: Time of arrival of the ray.
        interactions: Text description of the ray interactions.
        phase_in_degrees: Ray phase in degrees.
        interactions_positions: Text representation of the interaction positions.
        receiver_id: Foreign key referencing the associated receiver.
        receiver: Receiver object associated with this ray.
    """
    __tablename__ = 'rays'
    id = Column(Integer, primary_key=True)
    departure_elevation = Column(Float)
    departure_azimuth = Column(Float)
    arrival_elevation = Column(Float)
    arrival_azimuth = Column(Float)
    path_gain = Column(Float)
    time_of_arrival = Column(Float)
    interactions = Column(Text)
    phase_in_degrees = Column(Float)
    interactions_positions = Column(Text)
    receiver_id = Column(Integer, ForeignKey('receivers.id'))
    
    receiver = relationship("Receiver", back_populates="rays")

def create_database(dataBaseFileName='episodedata.db'):
    """
    Create a new SQLite database for storing ray-tracing episode data.

    If a database file with the same name already exists, it is removed before
    creating a new empty database. The function initializes all SQLAlchemy
    tables defined by the ORM models and returns an active database session.

    Args:
        dataBaseFileName: Path or filename of the SQLite database to be created.
            Defaults to ``"episodedata.db"``.

    Returns:
        A SQLAlchemy session connected to the newly created database.

    Raises:
        OSError: If the existing database file cannot be removed.
        SQLAlchemyError: If the database engine, tables, or session cannot be
            created.
    """
    if os.path.isfile(dataBaseFileName):
        os.remove(dataBaseFileName)
        print(colored(f'Removed old database: {dataBaseFileName}', color='red'))
    else:
        print('Created a empty database: ', dataBaseFileName)
    print('##############################')
    engine = create_engine('sqlite:///' + dataBaseFileName)
    
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    return Session()

def open_database(dataBaseFileName='episodedata.db'):
    """
    Open an existing SQLite database containing ray-tracing episode data.

    This function checks whether the specified database file exists, creates a
    SQLAlchemy engine, initializes ORM metadata if needed, and returns an active
    database session.

    Args:
        dataBaseFileName: Path or filename of the SQLite database to be opened.
            Defaults to ``"episodedata.db"``.

    Returns:
        A SQLAlchemy session connected to the existing database.

    Raises:
        SystemExit: If the database file does not exist.
        SQLAlchemyError: If the database engine, tables, or session cannot be
            created.
    """
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
