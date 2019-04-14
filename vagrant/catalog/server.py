#! $(which python3)

from flask import Flask, jsonify, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from db_setup import Base, User, Team, Player
import random

# instantiate Flask app
app = Flask(__name__)

# connect to the DB and get a session object
engine = create_engine('sqlite:///roster.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/api/v1/teams/')
def show_teams_json():
    '''
    API endpoint to list all teams in the DB.
    '''
    teams = session.query(Team).all()
    return jsonify(teams=[team.serialize for team in teams])


@app.route('/api/v1/players/')
def get_players_json():
    '''
    API endpoint to list all players in the DB.
    '''
    players = session.query(Player).all()
    return jsonify(players=[player.serialize for player in players])


@app.route('/')
@app.route('/teams/')
def show_teams():
    teams = session.query(Team).order_by(asc(Team.name))
    return render_template('public-teams.html', teams=teams)


@app.route('/teams/<string:team_nickname>/')
@app.route('/teams/<string:team_nickname>/players/')
def show_players(team_nickname):
    team = session.query(Team).filter_by(nickname=team_nickname).one()
    items = session.query(Player).filter_by(
        team_id=team.id).all()
    return render_template('public-players.html', items=items, team=team)


@app.route('/teams/<string:team_nickname>/new/', methods=['GET', 'POST'])
@app.route('/teams/<string:team_nickname>/players/new/', methods=[
    'GET', 'POST'])
def add_player(team_nickname):
    team = session.query(Team).filter_by(nickname=team_nickname).one()
    if request.method == 'POST':
        try:
            new_player = Player(
                name=request.form['name'],
                position=request.form['position'],
                jersey_number=int(request.form['jersey_number']),
                team_id=team.id
            )
            session.add(new_player)
        except Exception as ex:
            # TODO input validations
            pass
        try:
            session.commit()
        except IntegrityError as ex:
            pass
            # TODO treat non-unique jersey number
            # flash('That jersey number is already taken, please try again!')
        return redirect(url_for('show_players', team_nickname=team_nickname))
    elif request.method == 'GET':
        return render_template('new-player.html', team_nickname=team_nickname)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
