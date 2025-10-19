from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import re
import json
import pandas as pd
from datetime import datetime

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
        
        # First, remove duplicates by grouping by player + match_no + match_between
        # then aggregate by player to get totals
        pipeline = [
            # Step 1: Group by player, match_no, and match to remove duplicates
            {'$group': {
                '_id': {
                    'player': '$Batsman_Name',
                    'match_no': '$Match_no',
                    'match': '$Match_Between'
                },
                'runs': {'$first': '$Runs'},
                'balls': {'$first': '$Balls'},
                'fours': {'$first': '$4s'},
                'sixes': {'$first': '$6s'}
            }},
            # Step 2: Group by player to get totals
            {'$group': {
                '_id': '$_id.player',
                'total_runs': {'$sum': '$runs'},
                'total_balls': {'$sum': '$balls'},
                'total_4s': {'$sum': '$fours'},
                'total_6s': {'$sum': '$sixes'},
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

        # First, remove duplicates by grouping by bowler + match_no + match_between
        # then aggregate by bowler to get totals
        pipeline = [
            # Step 1: Group by bowler, match_no, and match to remove duplicates
            {'$group': {
                '_id': {
                    'bowler': '$Bowler_Name',
                    'match_no': '$Match_no',
                    'match': '$Match_Between'
                },
                'wickets': {'$first': '$Wickets'},
                'runs': {'$first': '$Runs'},
                'overs': {'$first': '$Overs'},
                'maidens': {'$first': '$Maidens'}
            }},
            # Step 2: Group by bowler to get totals
            {'$group': {
                '_id': '$_id.bowler',
                'total_wickets': {'$sum': '$wickets'},
                'total_runs': {'$sum': '$runs'},
                'overs_list': {'$push': '$overs'},  # Collect all overs to process
                'total_maidens': {'$sum': '$maidens'},
                'matches': {'$sum': 1}
            }},
            {'$sort': {'total_wickets': -1}},
            {'$limit': limit}
        ]

        raw_result = list(bowling_collection.aggregate(pipeline))

        # Process each bowler to correctly calculate total overs
        result = []
        for bowler in raw_result:
            # Convert cricket overs to balls and sum them up
            total_balls = 0
            for overs in bowler['overs_list']:
                # overs like 9.5 means 9 overs + 5 balls = (9*6) + 5 = 59 balls
                overs_int = int(overs)
                balls_remainder = int(round((overs - overs_int) * 10))  # Get decimal part as balls
                total_balls += (overs_int * 6) + balls_remainder

            # Convert total balls back to cricket overs format
            overs_bowled = total_balls // 6
            balls_bowled = total_balls % 6
            total_overs_cricket = float(f"{overs_bowled}.{balls_bowled}")

            # Calculate economy (runs per over)
            economy = (bowler['total_runs'] / total_balls * 6) if total_balls > 0 else 0

            result.append({
                'bowler': bowler['_id'],
                'total_wickets': bowler['total_wickets'],
                'total_runs': bowler['total_runs'],
                'total_overs': total_overs_cricket,
                'total_balls': total_balls,
                'total_maidens': bowler['total_maidens'],
                'matches': bowler['matches'],
                'economy': economy
            })

        return jsonify(result)
    except Exception as e:
        print(f"Error in get_top_bowlers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings"""
    s1, s2 = s1.lower(), s2.lower()
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def fuzzy_match(query, candidates, threshold=2):
    """Find candidates that match the query within a certain edit distance threshold"""
    matches = []
    query_lower = query.lower()

    for candidate in candidates:
        candidate_lower = candidate.lower()

        # Exact match gets highest priority
        if query_lower in candidate_lower:
            matches.append((candidate, 0))
        else:
            # Check if query matches any word in the candidate
            words = candidate_lower.split()
            min_distance = float('inf')

            for word in words:
                distance = levenshtein_distance(query_lower, word)
                min_distance = min(min_distance, distance)

            # Also check full name distance for short queries
            if len(query_lower) >= 3:
                full_distance = levenshtein_distance(query_lower, candidate_lower)
                min_distance = min(min_distance, full_distance)

            if min_distance <= threshold:
                matches.append((candidate, min_distance))

    # Sort by distance (closer matches first)
    matches.sort(key=lambda x: x[1])
    return [match[0] for match in matches]

@app.route('/api/search')
def natural_language_search():
    """Natural language search endpoint with fuzzy matching"""
    try:
        query = request.args.get('q', '').lower().strip()

        if not query:
            return jsonify({'error': 'Query parameter required'}), 400

        results = {
            'players': [],
            'matches': [],
            'stats': {}
        }

        # Get all unique player names and team names for fuzzy matching
        all_players = players_collection.distinct('player_name')
        all_teams = matches_collection.distinct('Team1')

        # Determine search threshold based on query length
        threshold = 1 if len(query) <= 4 else 2

        # Fuzzy match player names
        matched_players = fuzzy_match(query, all_players, threshold)

        # Fuzzy match team names
        matched_teams = fuzzy_match(query, all_teams, threshold)

        # Search patterns with fuzzy support
        if any(word in query for word in ['batsman', 'batter', 'runs', 'scored']):
            # Extract the name part from query
            name_query = ' '.join([word for word in query.split() if word not in ['batsman', 'batter', 'runs', 'scored', 'top', 'best']])

            if name_query:
                matched_players = fuzzy_match(name_query, all_players, threshold)

            if matched_players:
                results['players'] = list(batting_collection.aggregate([
                    {'$match': {'Batsman_Name': {'$in': matched_players}}},
                    {'$group': {
                        '_id': '$Batsman_Name',
                        'total_runs': {'$sum': '$Runs'}
                    }},
                    {'$sort': {'total_runs': -1}},
                    {'$limit': 10}
                ]))
            else:
                # Fallback to top batsmen
                results['players'] = list(batting_collection.aggregate([
                    {'$group': {
                        '_id': '$Batsman_Name',
                        'total_runs': {'$sum': '$Runs'}
                    }},
                    {'$sort': {'total_runs': -1}},
                    {'$limit': 5}
                ]))

        elif any(word in query for word in ['bowler', 'wickets', 'bowling']):
            # Extract the name part from query
            name_query = ' '.join([word for word in query.split() if word not in ['bowler', 'wickets', 'bowling', 'top', 'best']])

            if name_query:
                matched_players = fuzzy_match(name_query, all_players, threshold)

            if matched_players:
                results['players'] = list(bowling_collection.aggregate([
                    {'$match': {'Bowler_Name': {'$in': matched_players}}},
                    {'$group': {
                        '_id': '$Bowler_Name',
                        'total_wickets': {'$sum': '$Wickets'}
                    }},
                    {'$sort': {'total_wickets': -1}},
                    {'$limit': 10}
                ]))
            else:
                # Fallback to top bowlers
                results['players'] = list(bowling_collection.aggregate([
                    {'$group': {
                        '_id': '$Bowler_Name',
                        'total_wickets': {'$sum': '$Wickets'}
                    }},
                    {'$sort': {'total_wickets': -1}},
                    {'$limit': 5}
                ]))

        elif 'team' in query or matched_teams:
            # Use fuzzy matched team
            team_name = matched_teams[0] if matched_teams else None

            if team_name:
                results['players'] = list(players_collection.find({'team_name': {'$regex': f'^\\s*{re.escape(team_name)}\\s*$', '$options': 'i'}}, {'_id': 0}).limit(10))
                results['matches'] = list(matches_collection.find({'$or': [{'Team1': {'$regex': f'^\\s*{re.escape(team_name)}\\s*$', '$options': 'i'}}, {'Team2': {'$regex': f'^\\s*{re.escape(team_name)}\\s*$', '$options': 'i'}}]}, {'_id': 0}).limit(5))

        else:
            # General fuzzy search for players
            if matched_players:
                results['players'] = list(players_collection.find({'player_name': {'$in': matched_players}}, {'_id': 0}).limit(10))

            # General fuzzy search for matches (teams)
            if matched_teams:
                results['matches'] = list(matches_collection.find({'$or': [{'Team1': {'$in': matched_teams}}, {'Team2': {'$in': matched_teams}}]}, {'_id': 0}).limit(5))

        return jsonify(results)
    except Exception as e:
        print(f"Search error: {str(e)}")
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

        # Get player info including description and image
        player_info = players_collection.find_one(
            {'player_name': player_name},
            {'_id': 0, 'description': 1, 'team_name': 1, 'playingRole': 1, 'image_of_player': 1}
        )

        return jsonify({
            'player_name': player_name,
            'description': player_info.get('description', '') if player_info else '',
            'team': player_info.get('team_name', '') if player_info else '',
            'role': player_info.get('playingRole', '') if player_info else '',
            'image': player_info.get('image_of_player', '') if player_info else '',
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
        # Determine innings order based on which team appears first in collection
        match_team1 = match.get('Team1', '').strip()
        match_team2 = match.get('Team2', '').strip()

        first_innings_team = None
        team1_batting = []
        team2_batting = []

        for stat in batting_stats:
            team_innings = stat.get('Team_Innings', '').strip()

            # Capture the first team that appears in the collection
            if first_innings_team is None:
                first_innings_team = team_innings
                print(f"First innings team from collection: {first_innings_team}")

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

        # Determine innings order based on which team appeared first in collection
        # Check if first_innings_team matches Team2 (needs swap)
        team2_batted_first = False
        if first_innings_team:
            team2_batted_first = (
                first_innings_team == match_team2 or
                match_team2.find(first_innings_team) >= 0 or
                first_innings_team.find(match_team2) >= 0
            )

        if team2_batted_first:
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

@app.route('/api/best-moments')
def get_best_moments():
    """Get highlighted moments from the tournament"""
    try:
        moment_type = request.args.get('type', 'all')

        moments = []

        # CENTURIES (100+ runs)
        if moment_type in ['all', 'centuries']:
            centuries = list(batting_collection.find(
                {'Runs': {'$gte': 100}},
                {'_id': 0}
            ).sort('Runs', -1))

            for century in centuries:
                match = matches_collection.find_one({'Match_no': century['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'century',
                    'title': f"{century['Batsman_Name']} - Magnificent {century['Runs']}",
                    'description': f"Scored {century['Runs']} runs off {century['Balls']} balls with {century['4s']} fours and {century['6s']} sixes",
                    'player': century['Batsman_Name'],
                    'team': century['Team_Innings'],
                    'match_no': century['Match_no'],
                    'match': century.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'runs': century['Runs'],
                    'balls': century['Balls'],
                    'fours': century['4s'],
                    'sixes': century['6s'],
                    'strike_rate': century['Strike_Rate']
                })

        # HALF-CENTURIES (50-99 runs)
        if moment_type in ['all', 'fifties']:
            fifties = list(batting_collection.find(
                {'Runs': {'$gte': 50, '$lt': 100}},
                {'_id': 0}
            ).sort('Runs', -1).limit(30))

            for fifty in fifties:
                match = matches_collection.find_one({'Match_no': fifty['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'fifty',
                    'title': f"{fifty['Batsman_Name']} - Solid {fifty['Runs']}",
                    'description': f"Scored {fifty['Runs']} runs off {fifty['Balls']} balls",
                    'player': fifty['Batsman_Name'],
                    'team': fifty['Team_Innings'],
                    'match_no': fifty['Match_no'],
                    'match': fifty.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'runs': fifty['Runs'],
                    'balls': fifty['Balls'],
                    'fours': fifty['4s'],
                    'sixes': fifty['6s'],
                    'strike_rate': fifty['Strike_Rate']
                })

        # 5-WICKET HAULS
        if moment_type in ['all', 'wickets']:
            five_wickets = list(bowling_collection.find(
                {'Wickets': {'$gte': 5}},
                {'_id': 0}
            ).sort('Wickets', -1))

            for performance in five_wickets:
                match = matches_collection.find_one({'Match_no': performance['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'five_wickets',
                    'title': f"{performance['Bowler_Name']} - Devastating {performance['Wickets']}-wicket haul",
                    'description': f"Took {performance['Wickets']} wickets for {performance['Runs']} runs in {performance['Overs']} overs",
                    'player': performance['Bowler_Name'],
                    'team': performance['Bowling_Team'],
                    'match_no': performance['Match_no'],
                    'match': performance.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'wickets': performance['Wickets'],
                    'runs': performance['Runs'],
                    'overs': performance['Overs'],
                    'economy': performance['Economy']
                })

        # 4-WICKET HAULS
        if moment_type in ['all', 'wickets']:
            four_wickets = list(bowling_collection.find(
                {'Wickets': 4},
                {'_id': 0}
            ).sort('Runs', 1).limit(20))

            for performance in four_wickets:
                match = matches_collection.find_one({'Match_no': performance['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'four_wickets',
                    'title': f"{performance['Bowler_Name']} - Brilliant {performance['Wickets']}-wicket spell",
                    'description': f"Took {performance['Wickets']} wickets for {performance['Runs']} runs in {performance['Overs']} overs",
                    'player': performance['Bowler_Name'],
                    'team': performance['Bowling_Team'],
                    'match_no': performance['Match_no'],
                    'match': performance.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'wickets': performance['Wickets'],
                    'runs': performance['Runs'],
                    'overs': performance['Overs'],
                    'economy': performance['Economy']
                })

        # BIG HITTING (Most sixes in an innings)
        if moment_type in ['all', 'sixes']:
            big_hitters = list(batting_collection.find(
                {'6s': {'$gte': 3}},
                {'_id': 0}
            ).sort('6s', -1).limit(30))

            for performance in big_hitters:
                match = matches_collection.find_one({'Match_no': performance['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'big_hitting',
                    'title': f"{performance['Batsman_Name']} - {performance['6s']} Massive Sixes!",
                    'description': f"Smashed {performance['6s']} sixes while scoring {performance['Runs']} runs",
                    'player': performance['Batsman_Name'],
                    'team': performance['Team_Innings'],
                    'match_no': performance['Match_no'],
                    'match': performance.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'runs': performance['Runs'],
                    'sixes': performance['6s'],
                    'balls': performance['Balls'],
                    'fours': performance.get('4s', 0),
                    'strike_rate': performance.get('Strike_Rate', 0)
                })

        # ECONOMICAL BOWLING (Best economy rates for 4+ overs)
        if moment_type in ['all', 'economy']:
            economical = list(bowling_collection.find(
                {'Overs': {'$gte': 4}, 'Economy': {'$gt': 0}},
                {'_id': 0}
            ).sort('Economy', 1).limit(20))

            for performance in economical:
                match = matches_collection.find_one({'Match_no': performance['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'economical',
                    'title': f"{performance['Bowler_Name']} - Miserly {performance['Economy']} economy",
                    'description': f"Conceded just {performance['Runs']} runs in {performance['Overs']} overs at {performance['Economy']} economy",
                    'player': performance['Bowler_Name'],
                    'team': performance['Bowling_Team'],
                    'match_no': performance['Match_no'],
                    'match': performance.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'wickets': performance['Wickets'],
                    'runs': performance['Runs'],
                    'overs': performance['Overs'],
                    'economy': performance['Economy']
                })

        # EXPLOSIVE INNINGS (Strike rate > 150 for 30+ runs)
        if moment_type in ['all', 'explosive']:
            explosive = list(batting_collection.find(
                {'Runs': {'$gte': 30}, 'Strike_Rate': {'$gte': 150}},
                {'_id': 0}
            ).sort('Strike_Rate', -1).limit(25))

            for performance in explosive:
                match = matches_collection.find_one({'Match_no': performance['Match_no']}, {'_id': 0})
                moments.append({
                    'type': 'explosive',
                    'title': f"{performance['Batsman_Name']} - Explosive {performance['Strike_Rate']} SR",
                    'description': f"Blitzed {performance['Runs']} runs off just {performance['Balls']} balls",
                    'player': performance['Batsman_Name'],
                    'team': performance['Team_Innings'],
                    'match_no': performance['Match_no'],
                    'match': performance.get('Match_Between', 'Unknown'),
                    'venue': match['Venue'] if match else 'Unknown',
                    'runs': performance['Runs'],
                    'balls': performance['Balls'],
                    'strike_rate': performance['Strike_Rate']
                })

        return jsonify({'moments': moments, 'total': len(moments)})
    except Exception as e:
        print(f"Error fetching best moments: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/head-to-head')
def get_head_to_head():
    """Get head-to-head history between two teams"""
    try:
        team1 = request.args.get('team1', '')
        team2 = request.args.get('team2', '')
        limit = int(request.args.get('limit', 10))

        if not team1 or not team2:
            return jsonify({'error': 'Both team1 and team2 parameters are required'}), 400

        # Load ODI matches data
        csv_path = os.path.join(os.path.dirname(__file__), 'odi_Matches_Data.csv')

        if not os.path.exists(csv_path):
            return jsonify({'error': 'ODI matches data file not found'}), 404

        # Read CSV
        df = pd.read_csv(csv_path)

        # Filter matches between these two teams (both directions)
        h2h_matches = df[
            ((df['Team1 Name'] == team1) & (df['Team2 Name'] == team2)) |
            ((df['Team1 Name'] == team2) & (df['Team2 Name'] == team1))
        ].copy()

        # Sort by date descending (most recent first)
        h2h_matches['Match Date'] = pd.to_datetime(h2h_matches['Match Date'])
        h2h_matches = h2h_matches.sort_values('Match Date', ascending=False)

        # Limit to last N matches
        h2h_matches = h2h_matches.head(limit)

        # Prepare response
        matches = []
        for _, row in h2h_matches.iterrows():
            match_data = {
                'match_no': int(row['ODI Match No']) if pd.notna(row['ODI Match No']) else None,
                'match_name': row['Match Name'] if pd.notna(row['Match Name']) else 'Unknown',
                'series_name': row['Series Name'] if pd.notna(row['Series Name']) else 'Unknown',
                'match_date': row['Match Date'].strftime('%B %d, %Y') if pd.notna(row['Match Date']) else 'Unknown',
                'venue': f"{row['Match Venue (Stadium)']}, {row['Match Venue (City)']}" if pd.notna(row['Match Venue (Stadium)']) else 'Unknown',
                'team1': row['Team1 Name'] if pd.notna(row['Team1 Name']) else 'Unknown',
                'team1_score': f"{int(row['Team1 Runs Scored'])}/{int(row['Team1 Wickets Fell'])}" if pd.notna(row['Team1 Runs Scored']) and pd.notna(row['Team1 Wickets Fell']) else 'N/A',
                'team2': row['Team2 Name'] if pd.notna(row['Team2 Name']) else 'Unknown',
                'team2_score': f"{int(row['Team2 Runs Scored'])}/{int(row['Team2 Wickets Fell'])}" if pd.notna(row['Team2 Runs Scored']) and pd.notna(row['Team2 Wickets Fell']) else 'N/A',
                'winner': row['Match Winner'] if pd.notna(row['Match Winner']) else 'No Result',
                'result': row['Match Result Text'] if pd.notna(row['Match Result Text']) else 'No Result',
                'mom': row['MOM Player'] if pd.notna(row['MOM Player']) else 'Unknown'
            }
            matches.append(match_data)

        # Calculate head-to-head summary
        total_matches = len(matches)
        team1_wins = sum(1 for m in matches if m['winner'] == team1)
        team2_wins = sum(1 for m in matches if m['winner'] == team2)
        no_results = total_matches - team1_wins - team2_wins

        summary = {
            'total_matches': total_matches,
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'no_results': no_results,
            'team1': team1,
            'team2': team2
        }

        return jsonify({
            'success': True,
            'summary': summary,
            'matches': matches
        })

    except Exception as e:
        print(f"Error fetching head-to-head: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)