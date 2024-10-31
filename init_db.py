import sqlite3
import os

# Chemin vers la base de données SQLite
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

# Connexion à la base de données
conn = sqlite3.connect(db_path)

# Création de la table 'Tournament'
conn.execute('''
    CREATE TABLE Tournament (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    date_start DATE,
    date_end DATE,
    location VARCHAR(100)
    );
''')

conn.execute('''
    CREATE TABLE Equipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    logo VARCHAR(255),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(id) ON DELETE CASCADE);
''')

conn.execute('''
    CREATE TABLE "Groupe" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES Tournament(id) ON DELETE CASCADE);
''')

conn.execute('''
    CREATE TABLE Group_Team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES "Group"(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES Team(id) ON DELETE CASCADE);
''')

conn.execute('''
    CREATE TABLE "Match" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    group_id INTEGER,
    team1_id INTEGER NOT NULL,
    team2_id INTEGER NOT NULL,
    score_team1 INTEGER,
    score_team2 INTEGER,
    date DATE,
    time TIME,
    round VARCHAR(50),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES "Group"(id) ON DELETE CASCADE,
    FOREIGN KEY (team1_id) REFERENCES Team(id) ON DELETE CASCADE,
    FOREIGN KEY (team2_id) REFERENCES Team(id) ON DELETE CASCADE);
''')

conn.execute('''
    CREATE TABLE GroupStanding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    FOREIGN KEY (group_id) REFERENCES "Group"(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES Team(id) ON DELETE CASCADE);
''')

conn.execute('''
   CREATE TABLE KnockoutRound (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    round VARCHAR(50) NOT NULL,
    team1_id INTEGER NOT NULL,
    team2_id INTEGER NOT NULL,
    score_team1 INTEGER,
    score_team2 INTEGER,
    date DATE,
    time TIME,
    winner_team_id INTEGER,
    FOREIGN KEY (tournament_id) REFERENCES Tournament(id) ON DELETE CASCADE,
    FOREIGN KEY (team1_id) REFERENCES Team(id) ON DELETE CASCADE,
    FOREIGN KEY (team2_id) REFERENCES Team(id) ON DELETE CASCADE,
    FOREIGN KEY (winner_team_id) REFERENCES Team(id));
''')

# Fermer la connexion
conn.close()

print("Base de données initialisée avec succès.")
