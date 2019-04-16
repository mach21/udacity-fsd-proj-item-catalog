#! $(which python3)

from flask import Flask, jsonify, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
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


class DBError(Exception):
    status_code = 500

    def __init__(self, payload=None):
        Exception.__init__(self)
        self.message = 'Houston, we have a DB problem...'
        self.status_code = 500
        self.payload = payload

    def to_dict(self):
        rv = {}
        rv['traceback'] = self.payload or ''
        rv['message'] = self.message
        return rv


@app.errorhandler(DBError)
def handle_db_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/api/v1/teams/')
def show_teams_json():
    '''
    API endpoint to list all teams in the DB.
    '''
    session = DBSession()
    try:
        teams = session.query(Team).all()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return jsonify(teams=[team.serialize for team in teams])


@app.route('/api/v1/players/')
def get_players_json():
    '''
    API endpoint to list all players in the DB.
    '''
    session = DBSession()
    try:
        players = session.query(Player).all()
    except:
        session.rollback()
        raise DBError(payload=traceback.format_exc())
    finally:
        session.close()

    return jsonify(players=[player.serialize for player in players])


@app.route('/')
@app.route('/teams/')
def show_teams():
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


def is_jersey_number_valid(form_data, team_id):
    '''
    Utility method: jersey number validator
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

        # get new player data from form
        new_player = Player(
            name=bleach.clean(request.form['name']),
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
def edit_player(team_nickname, player_id):
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

        if request.form['name']:
            editedPlayer.name = bleach.clean(request.form['name'])
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
def delete_player(team_nickname, player_id):
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
    app.run(host='0.0.0.0', port=8000)
