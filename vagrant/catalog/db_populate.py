from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, User, Team, Player

engine = create_engine('sqlite:///roster.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


teams = [
    {
        'name': 'Anaheim Ducks',
        'nickname': 'ducks'
    },
    {
        'name': 'Arizona Coyotes',
        'nickname': 'coyotes'
    },
    {
        'name': 'Boston Bruins',
        'nickname': 'bruins'
    },
    {
        'name': 'Buffalo Sabres',
        'nickname': 'sabres'
    },
    {
        'name': 'Calgary Flames',
        'nickname': 'flames'
    },
    {
        'name': 'Carolina Hurricanes',
        'nickname': 'hurricanes'
    },
    {
        'name': 'Chicago Blackhawks',
        'nickname': 'blackhawks'
    },
    {
        'name': 'Colorado Avalanche',
        'nickname': 'avalanche'
    },
    {
        'name': 'Columbus Blue Jackets',
        'nickname': 'bluejackets'
    },
    {
        'name': 'Dallas Stars',
        'nickname': 'stars'
    },
    {
        'name': 'Detroit Red Wings',
        'nickname': 'redwings'
    },
    {
        'name': 'Edmonton Oilers',
        'nickname': 'oilers'
    },
    {
        'name': 'Florida Panthers',
        'nickname': 'panthers'
    },
    {
        'name': 'Los Angeles Kings',
        'nickname': 'kings'
    },
    {
        'name': 'Minnesota Wild',
        'nickname': 'wild'
    },
    {
        'name': 'Montreal Canadiens',
        'nickname': 'canadiens'
    },
    {
        'name': 'Nashville Predators',
        'nickname': 'predators'
    },
    {
        'name': 'New Jersey Devils',
        'nickname': 'devils'
    },
    {
        'name': 'New York Islanders',
        'nickname': 'islanders'
    },
    {
        'name': 'New York Rangers',
        'nickname': 'rangers'
    },
    {
        'name': 'Ottawa Senators',
        'nickname': 'senators'
    },
    {
        'name': 'Philadelphia Flyers',
        'nickname': 'flyers'
    },
    {
        'name': 'Pittsburgh Penguins',
        'nickname': 'penguins'
    },
    {
        'name': 'San Jose Sharks',
        'nickname': 'sharks'
    },
    {
        'name': 'St Louis Blues',
        'nickname': 'blues'
    },
    {
        'name': 'Tampa Bay Lightning',
        'nickname': 'lightning'
    },
    {
        'name': 'Toronto Maple Leafs',
        'nickname': 'mapleleafs'
    },
    {
        'name': 'Vancouver Canucks',
        'nickname': 'canucks'
    },
    {
        'name': 'Vegas Golden Knights',
        'nickname': 'goldenknights'
    },
    {
        'name': 'Washington Capitals',
        'nickname': 'caps'
    },
    {
        'name': 'Winnipeg Jets',
        'nickname': 'jets'
    }
]

# Add some users
lavi = User(name="Peter Laviolette", email="peter.laviolette@nhlpreds.com")
session.add(lavi)
session.commit()

trotz = User(name="Barry Trotz", email="trotzky@nyislanders.com")
session.add(trotz)
session.commit()

# Add the teams
for team in teams:
    session.add(Team(name=team['name'], nickname=team['nickname']))
    session.commit()

predators = session.query(Team).filter_by(nickname='predators').one()

# Add some preds
arvi = Player(
    user_id=1,
    name='Viktor Arvidsson',
    position='Offenceman',
    jersey_number=33,
    team=predators
)
session.add(arvi)
session.commit()

fil = Player(
    user_id=1,
    name='Filip Forsberg',
    position='Offenceman',
    jersey_number=9,
    team=predators
)
session.add(fil)
session.commit()

player = Player(
    user_id=1,
    name='Ryan Ellis',
    position='Defenceman',
    jersey_number=4,
    team=predators
)
session.add(player)
session.commit()

player = Player(
    user_id=1,
    name='Dan Hamhuis',
    position='Defenceman',
    jersey_number=5,
    team=predators
)
session.add(player)
session.commit()

player = Player(
    user_id=1,
    name='Pekka Rinne',
    position='Goaltender',
    jersey_number=35,
    team=predators
)
session.add(player)
session.commit()

player = Player(
    user_id=1,
    name='Juuse Saros',
    position='Goaltender',
    jersey_number=74,
    team=predators
)
session.add(player)
session.commit()

player = Player(
    user_id=1,
    name='Austin Watson',
    position='Offenceman',
    jersey_number=51,
    team=predators
)
session.add(player)
session.commit()

player = Player(
    user_id=1,
    name='Kyle Turris',
    position='Offenceman',
    jersey_number=8,
    team=predators
)
session.add(player)
session.commit()

# Add some islanders
greiss = Player(
    user_id=2,
    name='Thomas Greiss',
    position='Goaltender',
    jersey_number=1,
    team=session.query(Team).filter_by(nickname='islanders').one()
)
session.add(greiss)
session.commit()

print('Done populating DB.')
