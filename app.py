from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import re

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# MongoDB Connection
try:
    MONGO_URI = os.getenv('MONGO_URI')
    print(f"Connecting to MongoDB with URI: {MONGO_URI[:MONGO_URI.find('@')]}...")
    client = MongoClient(MONGO_URI)
    
    # Test the connection
    client.server_info()  # Will raise an exception if connection fails
    print("Successfully connected to MongoDB server")
    
    # List all database names
    print("Available databases:", client.list_database_names())
    
    # Connect to the specific database
    db_name = 'hello'
    db = client[db_name]
    print(f"Using database: {db_name}")
    
    # Initialize collections
    players_collection = db['WCPlayersInfoODIWC2023']
    matches_collection = db['matchScheduleResultsODIWC2023']
    batting_collection = db['battingODIWC2023']
    bowling_collection = db['bowlingODIWC2023']
    
    # List collections in the database
    print(f"Available collections in {db_name}:", db.list_collection_names())
    
except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    print("Please check your MONGO_URI in the .env file and ensure MongoDB is running")
    raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats/overview')
def get_overview():
    """Get dashboard overview statistics"""
    try:
        total_matches = matches_collection.count_documents({})
        total_players = players_collection.count_documents({})
        total_runs = batting_collection.aggregate([
            {'$group': {'_id': None, 'total': {'$sum': '$Runs'}}}
        ])
        total_wickets = bowling_collection.aggregate([
            {'$group': {'_id': None, 'total': {'$sum': '$Wickets'}}}
        ])
        
        runs_result = list(total_runs)
        wickets_result = list(total_wickets)
        
        return jsonify({
            'total_matches': total_matches,
            'total_players': total_players,
            'total_runs': runs_result[0]['total'] if runs_result else 0,
            'total_wickets': wickets_result[0]['total'] if wickets_result else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players')
def get_players():
    """Get all players with filtering"""
    try:
        team = request.args.get('team')
        role = request.args.get('role')
        search = request.args.get('search', '')
        
        query = {}
        if team:
            query['team_name'] = team
        if role:
            query['playingRole'] = role
        if search:
            query['player_name'] = {'$regex': search, '$options': 'i'}
        
        players = list(players_collection.find(query, {'_id': 0}))
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams')
def get_teams():
    """Get all unique teams"""
    try:
        teams = players_collection.distinct('team_name')
        return jsonify(sorted(teams))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches')
def get_matches():
    """Get all matches with optional filtering"""
    try:
        team = request.args.get('team')
        venue = request.args.get('venue')

        query = {}
        if team:
            # Use regex with trim to handle whitespace inconsistencies
            team_pattern = f'^\\s*{re.escape(team)}\\s*$'
            query['$or'] = [
                {'Team1': {'$regex': team_pattern, '$options': 'i'}},
                {'Team2': {'$regex': team_pattern, '$options': 'i'}}
            ]
        if venue:
            query['Venue'] = {'$regex': venue, '$options': 'i'}

        matches = list(matches_collection.find(query, {'_id': 0}).sort('Match_no', 1))
        return jsonify(matches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batting/top')
def get_top_batsmen():
    """Get top run scorers"""
    try:
        limit = int(request.args.get('limit', 10))
        
        pipeline = [
            {'$group': {
                '_id': '$Batsman_Name',
                'total_runs': {'$sum': '$Runs'},
                'total_balls': {'$sum': '$Balls'},
                'total_4s': {'$sum': '$4s'},
                'total_6s': {'$sum': '$6s'},
                'matches': {'$sum': 1}
            }},
            {'$project': {
                'batsman': '$_id',
                'total_runs': 1,
                'total_balls': 1,
                'total_4s': 1,
                'total_6s': 1,
                'matches': 1,
                'strike_rate': {
                    '$cond': [
                        {'$eq': ['$total_balls', 0]},
                        0,
                        {'$multiply': [{'$divide': ['$total_runs', '$total_balls']}, 100]}
                    ]
                }
            }},
            {'$sort': {'total_runs': -1}},
            {'$limit': limit}
        ]
        
        result = list(batting_collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bowling/top')
def get_top_bowlers():
    """Get top wicket takers"""
    try:
        limit = int(request.args.get('limit', 10))
        
        pipeline = [
            {'$group': {
                '_id': '$Bowler_Name',
                'total_wickets': {'$sum': '$Wickets'},
                'total_runs': {'$sum': '$Runs'},
                'total_overs': {'$sum': '$Overs'},
                'matches': {'$sum': 1}
            }},
            {'$project': {
                'bowler': '$_id',
                'total_wickets': 1,
                'total_runs': 1,
                'total_overs': 1,
                'matches': 1,
                'economy': {
                    '$cond': [
                        {'$eq': ['$total_overs', 0]},
                        0,
                        {'$divide': ['$total_runs', '$total_overs']}
                    ]
                }
            }},
            {'$sort': {'total_wickets': -1}},
            {'$limit': limit}
        ]
        
        result = list(bowling_collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def natural_language_search():
    """Natural language search endpoint"""
    try:
        query = request.args.get('q', '').lower()
        
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        results = {
            'players': [],
            'matches': [],
            'stats': {}
        }
        
        # Search patterns
        if any(word in query for word in ['batsman', 'batter', 'runs', 'scored']):
            results['players'] = list(batting_collection.aggregate([
                {'$match': {'Batsman_Name': {'$regex': query.split()[-1] if len(query.split()) > 1 else '', '$options': 'i'}}},
                {'$group': {
                    '_id': '$Batsman_Name',
                    'total_runs': {'$sum': '$Runs'}
                }},
                {'$sort': {'total_runs': -1}},
                {'$limit': 5}
            ]))
        
        elif any(word in query for word in ['bowler', 'wickets', 'bowling']):
            results['players'] = list(bowling_collection.aggregate([
                {'$match': {'Bowler_Name': {'$regex': query.split()[-1] if len(query.split()) > 1 else '', '$options': 'i'}}},
                {'$group': {
                    '_id': '$Bowler_Name',
                    'total_wickets': {'$sum': '$Wickets'}
                }},
                {'$sort': {'total_wickets': -1}},
                {'$limit': 5}
            ]))
        
        elif 'team' in query or any(team.lower() in query for team in ['india', 'australia', 'england', 'pakistan']):
            team_name = next((word.capitalize() for word in ['india', 'australia', 'england', 'pakistan', 'south africa'] if word in query), None)
            if team_name:
                results['players'] = list(players_collection.find({'team_name': {'$regex': team_name, '$options': 'i'}}, {'_id': 0}).limit(10))
                results['matches'] = list(matches_collection.find({'$or': [{'Team1': {'$regex': team_name, '$options': 'i'}}, {'Team2': {'$regex': team_name, '$options': 'i'}}]}, {'_id': 0}).limit(5))
        
        else:
            # General search
            results['players'] = list(players_collection.find({'player_name': {'$regex': query, '$options': 'i'}}, {'_id': 0}).limit(5))
            results['matches'] = list(matches_collection.find({'$or': [{'Team1': {'$regex': query, '$options': 'i'}}, {'Team2': {'$regex': query, '$options': 'i'}}]}, {'_id': 0}).limit(5))
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/venues')
def get_venues():
    """Get all unique venues"""
    try:
        venues = matches_collection.distinct('Venue')
        return jsonify(sorted(venues))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/performance/<path:player_name>')
def get_player_performance(player_name):
    """Get match-wise performance for a specific player"""
    try:
        # URL decode the player name (handles spaces and special characters)
        from urllib.parse import unquote
        player_name = unquote(player_name)

        print(f"Fetching performance for player: {player_name}")

        # Get batting performance
        batting_stats = list(batting_collection.find(
            {'Batsman_Name': player_name},
            {'_id': 0}
        ).sort('Match_no', 1))

        # Get bowling performance
        bowling_stats = list(bowling_collection.find(
            {'Bowler_Name': player_name},
            {'_id': 0}
        ).sort('Match_no', 1))

        print(f"Found {len(batting_stats)} batting records and {len(bowling_stats)} bowling records")

        # Get match details for context
        match_numbers = set()
        for stat in batting_stats:
            if 'Match_no' in stat:
                match_numbers.add(stat['Match_no'])
        for stat in bowling_stats:
            if 'Match_no' in stat:
                match_numbers.add(stat['Match_no'])

        # Fetch match details
        matches = {}
        if match_numbers:
            match_docs = matches_collection.find(
                {'Match_no': {'$in': list(match_numbers)}},
                {'_id': 0}
            )
            for match in match_docs:
                matches[match['Match_no']] = match

        # Combine batting stats with match info
        for stat in batting_stats:
            if stat.get('Match_no') in matches:
                stat['match_info'] = matches[stat['Match_no']]

        # Combine bowling stats with match info
        for stat in bowling_stats:
            if stat.get('Match_no') in matches:
                stat['match_info'] = matches[stat['Match_no']]

        return jsonify({
            'player_name': player_name,
            'batting': batting_stats,
            'bowling': bowling_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match/scorecard/<int:match_no>')
def get_match_scorecard(match_no):
    """Get detailed scorecard for a specific match"""
    try:
        print(f"Fetching scorecard for match: {match_no}")

        # Get match details
        match = matches_collection.find_one({'Match_no': match_no}, {'_id': 0})

        if not match:
            return jsonify({'error': 'Match not found'}), 404

        # Get batting performances for this match (sorted by batting position)
        batting_stats = list(batting_collection.find(
            {'Match_no': match_no},
            {'_id': 0}
        ).sort([('Batting_Position', 1)]))

        # Get bowling performances for this match
        bowling_stats = list(bowling_collection.find(
            {'Match_no': match_no},
            {'_id': 0}
        ).sort([('Bowler_Name', 1)]))

        # Group batting stats by team using Team_Innings field
        team1_batting = []
        team2_batting = []

        match_team1 = match.get('Team1', '').strip()
        match_team2 = match.get('Team2', '').strip()

        for stat in batting_stats:
            team_innings = stat.get('Team_Innings', '').strip()

            # Match team innings to Team1 or Team2
            if team_innings == match_team1 or match_team1.find(team_innings) >= 0 or team_innings.find(match_team1) >= 0:
                team1_batting.append(stat)
            elif team_innings == match_team2 or match_team2.find(team_innings) >= 0 or team_innings.find(match_team2) >= 0:
                team2_batting.append(stat)

        # Group bowling stats by team
        team1_bowling = []
        team2_bowling = []

        for stat in bowling_stats:
            bowler_name = stat.get('Bowler_Name', '')
            # Find player's team from players collection
            player = players_collection.find_one({'player_name': bowler_name}, {'team_name': 1, '_id': 0})

            if player:
                team_name = player.get('team_name', '').strip()

                # Match to Team1 or Team2
                if team_name == match_team1 or match_team1.find(team_name) >= 0 or team_name.find(match_team1) >= 0:
                    team1_bowling.append(stat)
                elif team_name == match_team2 or match_team2.find(team_name) >= 0 or team_name.find(match_team2) >= 0:
                    team2_bowling.append(stat)

        print(f"Found {len(team1_batting)} batting, {len(team1_bowling)} bowling for Team1")
        print(f"Found {len(team2_batting)} batting, {len(team2_bowling)} bowling for Team2")

        # Determine innings order based on number of batsmen
        # Team that batted first typically has more batsmen recorded (often all out)
        # Team that chased may have fewer batsmen (won with wickets in hand)
        if len(team2_batting) > len(team1_batting):
            # Swap teams so first innings is shown first
            print("Swapping team order - Team2 batted first")
            return jsonify({
                'match': match,
                'team1_batting': team2_batting,  # First innings
                'team2_batting': team1_batting,  # Second innings
                'team1_bowling': team2_bowling,
                'team2_bowling': team1_bowling,
                'team1_name': match_team2,  # Actual team name for first innings
                'team2_name': match_team1   # Actual team name for second innings
            })
        else:
            return jsonify({
                'match': match,
                'team1_batting': team1_batting,
                'team2_batting': team2_batting,
                'team1_bowling': team1_bowling,
                'team2_bowling': team2_bowling,
                'team1_name': match_team1,
                'team2_name': match_team2
            })
    except Exception as e:
        print(f"Error fetching match scorecard: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)