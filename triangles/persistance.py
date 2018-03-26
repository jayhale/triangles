from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref


Base = declarative_base()


class Configuration(Base):
    """Stores a unique board configuration"""
    __tablename__ = 'configurations'

    id = Column(Integer, primary_key=True)
    won = Column(Boolean, default=False, index=True)
    seq_confs = relationship('SeqConf', back_populates='configuration', lazy='dynamic')


class SeqConf(Base):
    """Stores a sequence-configuration association with ordering"""
    __tablename__ = 'sequences_configurations'

    sequence_id = Column(Integer, ForeignKey('sequences.id'), primary_key=True)
    sequence = relationship('Sequence', back_populates='seq_confs')
    configuration_id = Column(Integer, ForeignKey('configurations.id'), primary_key=True)
    configuration = relationship('Configuration', back_populates='seq_confs')
    order = Column(Integer)


class Sequence(Base):
    """Stores a sequence of moves"""
    __tablename__ = 'sequences'

    id = Column(Integer, primary_key=True)
    won = Column(Boolean, default=False)
    seq_confs = relationship('SeqConf', back_populates='sequence', lazy='dynamic')


class Transformation(Base):
    """Stores a transformation relationship between two configurations"""
    __tablename__ = 'transformations'

    from_configuration_id = Column(Integer, ForeignKey('configurations.id'), primary_key=True)
    from_configuration = relationship('Configuration', foreign_keys=from_configuration_id)
    to_configuration_id = Column(Integer, ForeignKey('configurations.id'), primary_key=True)
    to_configuration = relationship('Configuration', foreign_keys=to_configuration_id)
    desc = Column(String)
