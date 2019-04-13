from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Team(Base):
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format."""
        return {
            'id': self.id,
            'name': self.name
        }


class Player(Base):
    __tablename__ = 'player'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    position = Column(String(250), nullable=False)
    jersey_number = Column(Integer, nullable=False)
    team_id = Column(Integer, ForeignKey('team.id'))
    team = relationship(Team)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format."""
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'jersey_number': self.jersey_number
        }


engine = create_engine('sqlite:///roster.db')


Base.metadata.create_all(engine)
