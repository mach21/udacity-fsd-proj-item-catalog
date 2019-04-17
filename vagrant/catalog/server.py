#! $(which python3)

from flask import Flask, jsonify, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, User, Team, Player
import random
import bleach
import traceback

# instantiate Flask app
app = Flask(__name__)

# connect to the DB and get a session factory
engine = create_engine('sqlite:///roster.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


__DEBUG__ = False


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

    return render_template('teams.html', teams=teams)


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

    return render_template('players.html', items=items, team=team)


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
        team_nickname=team_nickname
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


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = __DEBUG__
    app.run(host='0.0.0.0', port=8000)
