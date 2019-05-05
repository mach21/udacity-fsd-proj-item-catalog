#! $(which python3)

from flask import Flask, jsonify, render_template, request, redirect
from flask import jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from db_setup import Base, User, Team, Player
import random
import string
import bleach
import traceback
import json
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'NHL Team Roster'
__DEBUG__ = True

app = Flask(__name__)

# connect to the DB and get a session factory
engine = create_engine('sqlite:///roster.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


class DBError(Exception):
    def __init__(self, payload=None):
        Exception.__init__(self)
        self.message = 'Houston, we have a DB problem...'
        self.status_code = 500
        self.payload = payload

    def to_dict(self):
        rv = {}
        if __DEBUG__:
            rv['traceback'] = self.payload or ''
        rv['message'] = self.message
        return rv


@app.errorhandler(DBError)
def handle_db_error(error):
    '''
    DB error handler.

    @param error: the caught error
    :returns: json-formatted error
    '''
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/api/v1/catalog.json')
def get_catalog_json():
    '''
    API endpoint to pretty-list the entire catalog.

    :returns: json-formatted catalog
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        teams = session.query(Team).all()
        players = session.query(Player).all()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    response = {'teams': []}
    for team in teams:
        t_players = [pl for pl in players if pl.team_id == team.id]
        response['teams'].append(
            {
                'id': team.id,
                'name': team.name,
                'nickname': team.nickname,
                'players': [
                    {
                        'id': player.id,
                        'name': player.name,
                        'jersery_number': player.jersey_number,
                        'position': player.position
                    } for player in t_players
                ]
            }
        )

    return jsonify(response)


@app.route('/login')
def show_login():
    '''
    show login route
    Set the session state and render the login page.

    :returns: render template
    '''
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


@app.route('/')
@app.route('/teams/')
def show_teams():
    '''
    show teams route
    Render the list of teams in the DB.

    :returns: render template
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        teams = session.query(Team).order_by(asc(Team.name))
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return render_template(
        'teams.html',
        teams=teams,
        login_session=login_session
    )


@app.route('/teams/<string:team_nickname>/')
@app.route('/teams/<string:team_nickname>/players/')
def show_players(team_nickname):
    '''
    show players route
    Render the list of players for a given team.

    @param team_nickname: the nickname of the team to list players for
    :returns: render template
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        team = session.query(Team).filter_by(nickname=team_nickname).one()
        items = session.query(Player).filter_by(
            team_id=team.id).all()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return render_template(
        'players.html',
        items=items,
        team=team,
        login_session=login_session
    )


@app.route('/teams/<string:team_nickname>/<int:player_id>')
@app.route('/teams/<string:team_nickname>/players/<int:player_id>')
def show_player(team_nickname, player_id):
    '''
    show player route
    Render the details of a given player.
    The route shows the team nickname for cosmetics only.

    @param player_id: the id of the player to show
    :returns: render template
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        player = session.query(Player).filter_by(id=player_id).one()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return render_template(
        'player.html',
        player=player,
        team_nickname=team_nickname,
        login_session=login_session
    )


def is_jersey_number_valid(form_data, team_id):
    '''
    Utility method: jersey number validator.

    @param form_data: the data collected from the user-submitted form
    @param team_id: the id of the team to check for unique jersey number
    :returns: (bool, int) tuple, where
        bool - signifies the jersey_number is either valid or invalid
        int - the jersey_number, if it is valid or already taken OR
              a numeric code if it is invalid
    :raises: DBError for any DB transaction issues
    '''

    # is integer
    try:
        jersey_number = int(
            bleach.clean(form_data['jersey_number'])
        )
    except ValueError:
        return (False, 1)

    # is between 1 and 99
    if not (jersey_number > 0 and jersey_number < 100):
        return (False, 2)

    # is not already taken
    session = DBSession()
    try:
        players = session.query(Player).filter_by(team_id=team_id).all()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    if jersey_number in [
        item.jersey_number for item in players
    ]:
        return (False, jersey_number)

    return (True, jersey_number)


@app.route('/teams/<string:team_nickname>/new/', methods=['GET', 'POST'])
@app.route('/teams/<string:team_nickname>/players/new/', methods=[
    'GET', 'POST'])
def add_player(team_nickname):
    '''
    new player route.
    GET: render the template to add a new player.
    POST: add a player to the DB.

    @param team_nickname: the nickname of the team to list players for
    :returns: render template
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        team = session.query(Team).filter_by(nickname=team_nickname).one()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    if request.method == 'POST':
        jersey_validity = is_jersey_number_valid(request.form, team.id)
        if jersey_validity[0]:
            jersey_number = jersey_validity[1]
        elif jersey_validity[1] in [1, 2]:
            flash('Jersey number must be an integer \
                between 1 and 99.')
            return render_template(
                'new-player.html',
                team_nickname=team_nickname
            )
        else:
            flash(
                'Jersey number {} is already taken! \
                Please try a different one.'.format(str(jersey_validity[1]))
            )
            return render_template(
                'new-player.html',
                team_nickname=team_nickname
            )

        # validate new player name isn't empty
        name = bleach.clean(request.form['name'])
        if name == '':
            flash(
                'Player name can not be empty! Please name this person.'
            )
            return render_template(
                'new-player.html',
                team_nickname=team_nickname
            )

        # compile new player data
        new_player = Player(
            name=name,
            position=bleach.clean(request.form['position']),
            jersey_number=jersey_number,
            team_id=team.id
        )

        session = DBSession()
        try:
            # add player to the DB
            session.add(new_player)
            session.commit()
        except:
            session.rollback()
            raise DBError(payload=traceback.format_exc())
        finally:
            session.close()

        flash('Player added.')
        return redirect(url_for(
            'show_players',
            team_nickname=team_nickname)
        )
    else:
        return render_template(
            'new-player.html',
            team_nickname=team_nickname
        )


@app.route('/teams/<string:team_nickname>/<int:player_id>/edit',
           methods=['GET', 'POST'])
@app.route('/teams/<string:team_nickname>/players/<int:player_id>/edit',
           methods=['GET', 'POST'])
def edit_player(team_nickname, player_id):
    '''
    edit player route.
    GET: render the template to edit a player.
    POST: edit the DB entry.

    @param team_nickname: the nickname of the team to list players for
    @param player_id: the id of the player to be edited
    :returns: render template
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        editedPlayer = session.query(Player).filter_by(id=player_id).one()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    if request.method == 'POST':
        jersey_validity = is_jersey_number_valid(
            request.form, editedPlayer.team_id
        )
        # good new jersey number, keep it
        if jersey_validity[0]:
            editedPlayer.jersey_number = jersey_validity[1]
        # bad jersey number format or lenght or something, complain
        elif jersey_validity[1] in [1, 2]:
            flash('Jersey number must be an integer \
                between 1 and 99.')
            return render_template(
                'edit-player.html',
                team_nickname=team_nickname,
                player_id=player_id,
                item=editedPlayer
            )
        # jersey number already taken
        else:
            jersey_number = jersey_validity[1]
            # taken by somebody else, complain
            if editedPlayer.jersey_number != jersey_number:
                flash(
                    'Jersey number {} is already taken! \
                    Please try a different one.'.format(
                        str(jersey_number)
                    )
                )
                return render_template(
                    'edit-player.html',
                    team_nickname=team_nickname,
                    player_id=player_id,
                    item=editedPlayer
                )
            # taken by the same player, keep it
            else:
                editedPlayer.jersey_number = jersey_number

        # validate new player name isn't empty
        name = bleach.clean(request.form['name'])
        if name == '':
            flash(
                'Player name can not be empty! Please name this person.'
            )
            return render_template(
                'edit-player.html',
                team_nickname=team_nickname,
                player_id=player_id,
                item=editedPlayer
            )
        editedPlayer.name = name

        if request.form['position']:
            editedPlayer.position = bleach.clean(request.form['position'])

        session = DBSession()
        try:
            session.add(editedPlayer)
            session.commit()
        except:
            session.rollback()
            raise DBError(payload=traceback.format_exc())
        finally:
            session.close()

        flash('Player edited.')
        return redirect(url_for(
            'show_players',
            team_nickname=team_nickname)
        )
    else:
        return render_template(
            'edit-player.html',
            team_nickname=team_nickname,
            player_id=player_id,
            item=editedPlayer
        )


@app.route('/teams/<string:team_nickname>/<int:player_id>/delete/',
           methods=['GET', 'POST'])
@app.route('/teams/<string:team_nickname>/players/<int:player_id>/delete/',
           methods=['GET', 'POST'])
def delete_player(team_nickname, player_id):
    '''
    delete player route.
    GET: render the template to delete a player.
    POST: delete the DB entry.

    @param team_nickname: the nickname of the team to list players for
    @param player_id: the id of the player to be deleted
    :returns: render template
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        itemToDelete = session.query(Player).filter_by(id=player_id).one()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    if request.method == 'POST':
        session = DBSession()
        try:
            session.delete(itemToDelete)
            session.commit()
        except:
            session.rollback()
            raise DBError(payload=traceback.format_exc())
        finally:
            session.close()

        flash('Player deleted.')
        return redirect(url_for(
            'show_players',
            team_nickname=team_nickname)
        )
    else:
        return render_template(
            'delete-player.html',
            item=itemToDelete,
            team_nickname=team_nickname
        )


def create_user(login_session):
    '''
    create a new user

    @param login_session: an instance of login_session
    :returns: the creaded user's id
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        session.add(User(
            name=login_session['username'],
            email=login_session['email']
        ))
        session.commit()
        user = session.query(User).filter_by(
            email=login_session['email']
        ).one()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return user.id


def get_user_info(user_id):
    '''
    get details about the user identified by user_id

    @param user_id: the user_id
    :returns: the db row entry
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        user = session.query(User).filter_by(id=user_id).one()
    except:
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return user


def get_user_id(email):
    '''
    get a user's id based on their email address

    @param email: the user email address
    :returns: user.id or None
    :raises: DBError for any DB transaction issues
    '''
    session = DBSession()
    try:
        user = session.query(User).filter_by(email=email).one_or_none()
    except:
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return user.id if user is not None else None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    result = requests.get(url).json()

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = get_user_id(data["email"])
    if user_id is None:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("You are now logged in as {}".format(login_session['username']))

    return output


@app.route('/disconnect')
def disconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None or login_session.get('username') is None:
        return redirect(url_for('show_teams'))

    # Invalidate access token
    requests.post(
        'https://accounts.google.com/o/oauth2/revoke',
        params={'token': access_token},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )

    del login_session['username']
    del login_session['email']
    del login_session['user_id']

    return redirect(url_for('show_teams'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = __DEBUG__
    app.run(host='0.0.0.0', port=8000)
