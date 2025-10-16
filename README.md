# ODI World Cup 2023 Dashboard

A comprehensive web-based dashboard for exploring and analyzing statistics from the 2023 ODI Cricket World Cup. This interactive application provides detailed insights into player performance, match results, and tournament statistics.

## Overview

This project is a Flask-based web application that visualizes cricket statistics from the ODI World Cup 2023. It features interactive charts, filterable tables, and a natural language search interface to explore player and match data stored in a MongoDB database.

## Features

### 1. **Dashboard Overview**
- Total matches played
- Total players participated
- Aggregate runs scored
- Total wickets taken

### 2. **Players Section**
- Browse all World Cup 2023 players
- Filter by team (India, Australia, England, etc.)
- Filter by role (Batter, Bowler, Allrounder, etc.)
- View player details including batting style and bowling style

### 3. **Matches Section**
- Complete match schedule and results
- Filter matches by team
- Filter by venue
- View match details including teams, dates, venues, and winners

### 4. **Top Batsmen**
- Interactive bar chart of top run scorers
- Detailed statistics table with:
  - Total runs scored
  - Balls faced
  - Boundaries (4s and 6s)
  - Strike rate
  - Number of matches played
- **Click on any bar** to highlight that player's row in the table

### 5. **Top Bowlers**
- Interactive bar chart of top wicket takers
- Detailed bowling statistics including:
  - Total wickets taken
  - Runs conceded
  - Overs bowled
  - Economy rate
  - Matches played
- **Click on any bar** to highlight that bowler's row in the table

### 6. **Natural Language Search**
- Search for players by name
- Find matches by team name
- Query statistics using natural language

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: MongoDB (cloud-hosted on MongoDB Atlas)
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js for interactive visualizations
- **Styling**: Custom CSS with gradient designs

## Project Structure

```
ODIWC2023/
├── app.py                          # Main Flask application
├── templates/
│   └── index.html                  # Frontend dashboard
├── .env                            # Environment variables (MongoDB credentials)
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
├── batting_summary.csv             # Batting statistics data
├── bowling_summary.csv             # Bowling statistics data
├── match_schedule_results.csv      # Match schedule and results
└── world_cup_players_info.csv      # Player information
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MongoDB Atlas account (or local MongoDB instance)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd ODIWC2023
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

Replace `<username>`, `<password>`, and `<cluster>` with your MongoDB credentials.

### Step 5: Import Data to MongoDB
Make sure your MongoDB database has the following collections:
- `WCPlayersInfoODIWC2023` - Player information
- `matchScheduleResultsODIWC2023` - Match data
- `battingODIWC2023` - Batting statistics
- `bowlingODIWC2023` - Bowling statistics

### Step 6: Run the Application
```bash
python app.py
```

The application will start on **http://localhost:5001**

> **Note**: Port 5001 is used instead of 5000 to avoid conflicts with macOS AirPlay Receiver.

## Usage

1. **Open your browser** and navigate to `http://localhost:5001`
2. **Explore the dashboard** using the navigation tabs
3. **Filter data** using the dropdown menus in Players and Matches sections
4. **Click on chart bars** to highlight specific players in the tables
5. **Search** using the search bar for quick lookups

## API Endpoints

The application provides the following REST API endpoints:

- `GET /` - Main dashboard page
- `GET /api/stats/overview` - Overview statistics
- `GET /api/players` - Get all players (with optional filters)
- `GET /api/teams` - Get list of all teams
- `GET /api/matches` - Get all matches (with optional filters)
- `GET /api/venues` - Get list of all venues
- `GET /api/batting/top` - Get top batsmen statistics
- `GET /api/bowling/top` - Get top bowlers statistics
- `GET /api/search?q=<query>` - Natural language search

## Data Sources

The data includes:
- **48 matches** from the ODI World Cup 2023
- **200+ players** from 11 participating teams
- Comprehensive batting and bowling statistics for all matches

## Key Features Explained

### Interactive Highlighting
When you click on a bar in the batting or bowling charts:
- The corresponding row in the table is highlighted with a yellow background
- The page automatically scrolls to show the highlighted row
- Only one row is highlighted at a time

### Smart Filtering
The application handles data inconsistencies:
- Team name filtering works despite whitespace variations in the database
- Case-insensitive searches
- Regex-based matching for flexible queries

### Responsive Design
- Mobile-friendly layout
- Adapts to different screen sizes
- Smooth animations and transitions

## Troubleshooting

### Port Already in Use
If you get a port conflict error, macOS AirPlay might be using port 5000. The app is configured to use port 5001, but you can also:
- Disable AirPlay Receiver in System Settings > General > AirDrop & Handoff
- Change the port in `app.py` (line 265)

### MongoDB Connection Issues
- Verify your MongoDB URI in the `.env` file
- Check that your IP address is whitelisted in MongoDB Atlas
- Ensure the database name is correct (`hello` in this project)

### Missing Dependencies
If you encounter module errors:
```bash
pip install -r requirements.txt
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source and available for educational purposes.

## Author

Devang Kankaria

## Acknowledgments

- Cricket data sourced from official ODI World Cup 2023 records
- Built with Flask and Chart.js
- Hosted on MongoDB Atlas

