from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, User, Team, Player

engine = create_engine('sqlite:///roster.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add user
lavi = User(name="Peter Laviolette", email="peter.laviolette@nhlpreds.com")
session.add(lavi)
session.commit()

# Add team
preds = Team(user_id=1, name="Nashville Predators")
session.add(preds)
session.commit()

# Add some players
arvi = Player(user_id=1, name="Viktor Arvidsson", position="Right Wing", jersey_number=33, team=preds)
session.add(arvi)
session.commit()

fil = Player(user_id=1, name="Filip Forsberg", position="Left Wing", jersey_number=9, team=preds)
session.add(fil)
session.commit()

print('Done populating DB.')