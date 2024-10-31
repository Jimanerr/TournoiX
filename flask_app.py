import os
import sqlite3
import math
import random
from flask import Flask, render_template, request, redirect, url_for, send_file
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Chemin vers la base de données
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    """Fonction pour établir une connexion à la base de données."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return conn

def get_tournois():
    """Fonction qui renvoi tout lestournois"""
    conn = get_db_connection()
    tournois = conn.execute('SELECT * FROM Tournament').fetchall()
    conn.close()
    return tournois
def get_data_tournoi(tournoi_id):
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM Tournament WHERE id = ?', (tournoi_id,)).fetchall()
    conn.close()
    return data

def get_equipes(tournoi_id):
    conn = get_db_connection()
    equipes = conn.execute('SELECT * FROM Equipe WHERE tournament_id = ?', (tournoi_id,)).fetchall()
    conn.close()
    return equipes

def get_groupes(tournoi_id):
    conn = get_db_connection()
    groupes = conn.execute('SELECT * FROM Groupe WHERE tournament_id = ?', (tournoi_id,)).fetchall()
    conn.close()
    return groupes

def get_matchs(tournoi_id):
    """Fonction qui renvoie tous les matchs d'un tournoi avec les noms des équipes."""
    conn = get_db_connection()
    matchs = conn.execute('''
        SELECT 
            m.id, 
            m.tournament_id, 
            m.group_id, 
            m.score_team1, 
            m.score_team2, 
            m.date, 
            m.time, 
            m.round, 
            t1.name AS team1_name, 
            t2.name AS team2_name 
        FROM 
            Match m
        JOIN 
            Equipe t1 ON m.team1_id = t1.id
        JOIN 
            Equipe t2 ON m.team2_id = t2.id
        WHERE 
            m.tournament_id = ?
    ''', (tournoi_id,)).fetchall()
    conn.close()
    return matchs

def get_equipe_par_groupe(group_id):
    conn = get_db_connection()
    equipes = conn.execute('''
            SELECT e.id FROM Equipe e
            JOIN Group_Team gt ON e.id = gt.team_id
            WHERE gt.group_id = ?
        ''', (group_id,)).fetchall()
    return equipes

def get_groupes_with_standing(tournoi_id):
    conn = get_db_connection()
    
    # Récupérer les groupes du tournoi
    groupes = conn.execute('SELECT id, name FROM Groupe WHERE tournament_id = ?', (tournoi_id,)).fetchall()

    # Pour chaque groupe, récupérer les équipes avec leur classement
    groupes_with_standing = []
    for groupe in groupes:
        groupe_id = groupe['id']
        
        # Récupérer les équipes avec leur classement dans GroupStanding
        standings = conn.execute('''
            SELECT e.name AS team_name, 
                   gs.matches_played, 
                   gs.wins, 
                   gs.draws, 
                   gs.losses, 
                   gs.goals_for, 
                   gs.goals_against, 
                   gs.goal_difference, 
                   gs.points
            FROM GroupStanding gs
            JOIN Equipe e ON gs.team_id = e.id
            WHERE gs.group_id = ?
            ORDER BY gs.points DESC, gs.goal_difference DESC, gs.goals_for DESC
        ''', (groupe_id,)).fetchall()

        # Ajouter le groupe et ses équipes classées
        groupes_with_standing.append({
            'groupe_id': groupe_id,
            'groupe_name': groupe['name'],
            'standings': standings
        })

    conn.close()
    return groupes_with_standing

@app.route('/')
def index():
    """Route pour la page d'accueil qui affiche les tournois."""
    tournois = get_tournois()
    return render_template('index.html', tournois=tournois)

@app.route('/create', methods=('GET', 'POST'))
def create():
    """Route pour créer un nouveau tournoi."""
    if request.method == 'POST':
        name = request.form['name']
        sport = request.form['sport']
        date_start = request.form['date_start']
        date_end = request.form['date_end']
        location = request.form['location']

        conn = get_db_connection()
        conn.execute('INSERT INTO Tournament (name, sport, date_start, date_end, location ) VALUES (?, ?, ?, ?, ?)', (name, sport, date_start, date_end, location))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/view_tournoi/<int:tournoi_id>', methods=('GET', 'POST'))
def tournoi(tournoi_id):
    """Route vers une nouvelle page avec les équipes, les matchs, et les infos d'un tournoi."""
    tournoi_data = get_data_tournoi(tournoi_id)
    groupes = get_groupes(tournoi_id)
    matchs = get_matchs(tournoi_id)

    # Récupération des équipes avec leur groupe
    conn = get_db_connection()
    equipes = conn.execute('''
        SELECT e.id, e.name, gt.group_id
        FROM Equipe e
        LEFT JOIN Group_Team gt ON e.id = gt.team_id
        WHERE e.tournament_id = ?
    ''', (tournoi_id,)).fetchall()
    conn.close()

    # Créer un dictionnaire pour stocker les groupes et leurs équipes
    equipes_par_groupe = {groupe['id']: {'name': groupe['name'], 'equipes': []} for groupe in groupes}

    # Associer les équipes à leurs groupes
    for equipe in equipes:
        group_id = equipe['group_id']
        if group_id is not None and group_id in equipes_par_groupe:
            equipes_par_groupe[group_id]['equipes'].append(equipe)

    # Convertir le dictionnaire en une liste pour passer au template
    groupes_avec_equipes = [{'id': g_id, 'name': g['name'], 'equipes': g['equipes']} for g_id, g in equipes_par_groupe.items()]
    
    # Partie classement:
    groupes_with_standing = get_groupes_with_standing(tournoi_id)
    return render_template('tournoi.html', groupes_classement=groupes_with_standing, tournoi_data=tournoi_data[0], groupes=groupes_avec_equipes, matchs=matchs)

@app.route('/ajouter_une_equipe/<int:tournoi_id>', methods=('GET', 'POST'))
def add_equipe(tournoi_id):
    """Route pour ajouter une équipe à un tournoi."""
    if request.method == 'POST':
        name = request.form['name']
        logo = request.form['logo']

        conn = get_db_connection()
        conn.execute('INSERT INTO Equipe (tournament_id, name, logo) VALUES (?, ?, ?)', (tournoi_id, name, logo))
        conn.commit()
        conn.close()
        return redirect(url_for('tournoi', tournoi_id=tournoi_id ))

    return render_template('add_equipe.html')

@app.route('/ajouter_un_groupe/<int:tournoi_id>', methods=('GET', 'POST'))
def add_groupe(tournoi_id):
    """Route pour ajouter un groupe à un tournoi."""
    if request.method == 'POST':
        name = request.form['name']

        conn = get_db_connection()
        conn.execute('INSERT INTO Groupe (name, tournament_id) VALUES (?, ?)', (name, tournoi_id))
        conn.commit()
        conn.close()
        return redirect(url_for('tournoi', tournoi_id=tournoi_id ))

    return render_template('add_groupe.html')
@app.route('/ajouter_un_match/<int:tournoi_id>', methods=('GET', 'POST'))
def add_match(tournoi_id):
    """Route pour ajouter un match à un tournoi."""
    equipes = get_equipes(tournoi_id)
    if request.method == 'POST':
        equipe1 = request.form['equipe1']
        equipe2 = request.form['equipe2']
        date = request.form['date']
        heurre = request.form['heurre']
        rang = request.form['round']

        conn = get_db_connection()
        conn.execute('INSERT INTO Match (tournament_id, team1_id, team2_id, score_team1, score_team2, date, time, round) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (tournoi_id, equipe1, equipe2, 0, 0, date, heurre, rang))
        conn.commit()
        conn.close()
        return redirect(url_for('tournoi', tournoi_id=tournoi_id ))

    return render_template('add_match.html', equipes=equipes)


@app.route('/repartition_auto/<int:tournoi_id>', methods=['POST'])
def repartition_auto(tournoi_id):
    conn = get_db_connection()

    # Récupérer les équipes et les groupes
    equipes = conn.execute('SELECT id, name FROM Equipe WHERE tournament_id = ?', (tournoi_id,)).fetchall()
    groupes = conn.execute('SELECT id, name FROM Groupe WHERE tournament_id = ?', (tournoi_id,)).fetchall()

    conn.close()

    # Calcul du nombre d'équipes et de groupes
    nombre_equipes = len(equipes)
    nombre_groupes = len(groupes)

    # Réinitialiser les affectations de groupes avant la nouvelle répartition
    conn = get_db_connection()
    conn.execute('DELETE FROM GroupStanding WHERE team_id IN (SELECT id FROM Equipe WHERE tournament_id = ?)', (tournoi_id,))

    conn.execute('DELETE FROM Group_Team WHERE team_id IN (SELECT id FROM Equipe WHERE tournament_id = ?)', (tournoi_id,))
    conn.execute('DELETE FROM Match WHERE tournament_id = ?', (tournoi_id,))

    conn.commit()

    # Répartir les équipes aléatoirement dans les groupes
    random.shuffle(equipes)  # Mélange aléatoire des équipes
    index_groupe = 0

    for equipe in equipes:
        group_id = groupes[index_groupe]['id']
        conn.execute('INSERT INTO Group_Team (group_id, team_id) VALUES (?, ?)', (group_id, equipe['id']))
        conn.execute('INSERT INTO GroupStanding (group_id, team_id) VALUES (?, ?)', (group_id, equipe['id']))

        index_groupe = (index_groupe + 1) % nombre_groupes

    conn.commit()
    conn.close()

    # Vérifier si le nombre d'équipes est un multiple du nombre de groupes au carré
    if math.sqrt(nombre_equipes) != nombre_groupes:
        bypass_message = "Attention : Le nombre d'équipes n'est pas un carré parfait par rapport au nombre de groupes. Cela peut entraîner des bypass lors des phases finales."
    else:
        bypass_message = "Les équipes ont été réparties aléatoirement dans les groupes."

    # Redirection avec un message de bypass si nécessaire
    return redirect(url_for('tournoi', tournoi_id=tournoi_id, bypass_message=bypass_message))

@app.route('/repartition_manuelle/<int:tournoi_id>', methods=['GET', 'POST'])
def repartition_manuelle(tournoi_id):
    conn = get_db_connection()

    if request.method == 'POST':
        # Supprimer toutes les répartitions actuelles des équipes dans les groupes pour ce tournoi
        conn.execute('DELETE FROM Group_Team WHERE team_id IN (SELECT id FROM Equipe WHERE tournament_id = ?)', (tournoi_id,))

        conn.commit()

        # Logique pour récupérer les choix de groupe pour chaque équipe
        for equipe_id in request.form:
            group_id = request.form[equipe_id]
            conn.execute('INSERT INTO Group_Team (group_id, team_id) VALUES (?, ?)', (group_id, equipe_id))
            conn.execute('DELETE FROM GroupStanding WHERE team_id = ?', (equipe_id,))

            conn.execute('INSERT INTO GroupStanding (group_id, team_id) VALUES (?, ?)', (group_id, equipe_id))

        conn.commit()
        conn.close()

        # Redirection après soumission
        return redirect(url_for('tournoi', tournoi_id=tournoi_id))

    # Récupérer les équipes et les groupes pour le formulaire de répartition
    equipes = conn.execute('SELECT id, name FROM Equipe WHERE tournament_id = ?', (tournoi_id,)).fetchall()
    groupes = conn.execute('SELECT id, name FROM Groupe WHERE tournament_id = ?', (tournoi_id,)).fetchall()

    # Récupérer l'affectation actuelle des équipes dans les groupes
    affectations = conn.execute('''
        SELECT Group_Team.team_id, Group_Team.group_id 
        FROM Group_Team
        JOIN Equipe ON Equipe.id = Group_Team.team_id
        WHERE Equipe.tournament_id = ?
    ''', (tournoi_id,)).fetchall()

    # Construire un dictionnaire {team_id: group_id} pour connaître le groupe actuel de chaque équipe
    groupe_actuel = {affectation['team_id']: affectation['group_id'] for affectation in affectations}

    conn.close()

    # Passer les équipes, les groupes et l'affectation actuelle au template
    return render_template('repartition_manuelle.html', equipes=equipes, groupes=groupes, groupe_actuel=groupe_actuel, tournoi_id=tournoi_id)

@app.route('/repartition_matchs_auto/<int:tournoi_id>', methods=['POST'])
def repartition_matchs_auto(tournoi_id):
    """Génère des matchs automatiquement pour toutes les équipes dans chaque groupe."""
    conn = get_db_connection()
    conn.execute('DELETE FROM Match WHERE tournament_id = ?', (tournoi_id,))
    conn.commit()  # Valider la suppression
    print("test")
    groupes = conn.execute('SELECT id FROM Groupe WHERE tournament_id = ?', (tournoi_id,)).fetchall()
    
    for groupe in groupes:
        group_id = groupe['id']
        
        equipes = get_equipe_par_groupe(group_id)

        for i in range(len(equipes)):
            for j in range(i + 1, len(equipes)):
                conn.execute(''' 
                    INSERT INTO Match (tournament_id, team1_id, team2_id, date, time, round)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (tournoi_id, equipes[i]['id'], equipes[j]['id'], '2024-10-23', '12:00', 1))  # Exemple de date et heure

    conn.commit()
    conn.close()

    return redirect(url_for('tournoi', tournoi_id=tournoi_id))
@app.route('/modifier_match/<int:match_id>/<int:tournoi_id>', methods=['GET', 'POST'])
def modifier_match(match_id, tournoi_id):
    conn = get_db_connection()

    # Récupérer les détails du match existant pour recalculer les standings si nécessaire
    match = conn.execute('SELECT * FROM Match WHERE id = ?', (match_id,)).fetchone()

    if request.method == 'POST':
        # Récupérer les données du formulaire
        score_team1 = int(request.form['score_team1'])
        score_team2 = int(request.form['score_team2'])
        date = request.form['date']
        time = request.form['time']
        
        team1_id = match['team1_id']
        team2_id = match['team2_id']

        # Vérifier si le match avait un score précédemment enregistré (pour savoir si c'était un match déjà joué)
        match_previously_played = (match['score_team1'] is not None and match['score_team2'] is not None)

        # Étape 1: Retirer les anciennes stats du match précédent (si les scores ont changé)
        if match_previously_played:
            previous_score_team1 = match['score_team1']
            previous_score_team2 = match['score_team2']
            
            # Mise à jour pour enlever les anciennes données dans GroupStanding
            update_team_stats(conn, team1_id, team2_id, previous_score_team1, previous_score_team2, inverse=True)

        # Étape 2: Ajouter les nouvelles stats basées sur les nouveaux scores
        update_team_stats(conn, team1_id, team2_id, score_team1, score_team2, inverse=False, match_previously_played=match_previously_played)

        # Étape 3: Mettre à jour le match dans la base de données avec les nouveaux scores
        conn.execute('''
            UPDATE Match
            SET score_team1 = ?, score_team2 = ?, date = ?, time = ?
            WHERE id = ?
        ''', (score_team1, score_team2, date, time, match_id))

        conn.commit()
        conn.close()

        return redirect(url_for('tournoi', tournoi_id=tournoi_id))  # Redirige vers la page du tournoi

    if match is None:
        return "Match non trouvé", 404

    return render_template('modifier_match.html', match=match, tournoi_id=tournoi_id)


# Fonction pour mettre à jour les statistiques des équipes après un match
def update_team_stats(conn, team1_id, team2_id, score_team1, score_team2, inverse=False, match_previously_played=False):
    # Calcul des résultats du match
    if score_team1 > score_team2:
        team1_points = 3
        team2_points = 0
        team1_win = 1
        team2_win = 0
        team1_draw = 0
        team2_draw = 0
        team1_loss = 0
        team2_loss = 1
    elif score_team1 < score_team2:
        team1_points = 0
        team2_points = 3
        team1_win = 0
        team2_win = 1
        team1_draw = 0
        team2_draw = 0
        team1_loss = 1
        team2_loss = 0
    else:
        team1_points = 1
        team2_points = 1
        team1_win = 0
        team2_win = 0
        team1_draw = 1
        team2_draw = 1
        team1_loss = 0
        team2_loss = 0

    # Si inverse est True, on retire les statistiques (retrait des anciens résultats)
    if inverse:
        # Inverser les valeurs pour annuler les résultats
        team1_points = -team1_points
        team2_points = -team2_points
        score_team1 = -score_team1
        score_team2 = -score_team2
        team1_win = -team1_win
        team2_win = -team2_win
        team1_draw = -team1_draw
        team2_draw = -team2_draw
        team1_loss = -team1_loss
        team2_loss = -team2_loss

    # Mettre à jour les statistiques de l'équipe 1
    conn.execute('''
        UPDATE GroupStanding
        SET wins = wins + ?,
            draws = draws + ?,
            losses = losses + ?,
            goals_for = goals_for + ?,
            goals_against = goals_against + ?,
            goal_difference = goal_difference + ?,
            points = points + ?
        WHERE team_id = ?
    ''', (
        team1_win,                         # Victoire de l'équipe 1
        team1_draw,                        # Match nul
        team1_loss,                        # Défaite de l'équipe 1
        score_team1,                       # Buts marqués par l'équipe 1
        score_team2,                       # Buts encaissés par l'équipe 1
        score_team1 - score_team2,         # Différence de buts
        team1_points,                      # Points gagnés par l'équipe 1
        team1_id                           # ID de l'équipe 1
    ))

    # Mettre à jour les statistiques de l'équipe 2
    conn.execute('''
        UPDATE GroupStanding
        SET wins = wins + ?,
            draws = draws + ?,
            losses = losses + ?,
            goals_for = goals_for + ?,
            goals_against = goals_against + ?,
            goal_difference = goal_difference + ?,
            points = points + ?
        WHERE team_id = ?
    ''', (
        team2_win,                         # Victoire de l'équipe 2
        team2_draw,                        # Match nul
        team2_loss,                        # Défaite de l'équipe 2
        score_team2,                       # Buts marqués par l'équipe 2
        score_team1,                       # Buts encaissés par l'équipe 2
        score_team2 - score_team1,         # Différence de buts
        team2_points,                      # Points gagnés par l'équipe 2
        team2_id                           # ID de l'équipe 2
    ))

    # Mettre à jour le nombre de matchs joués uniquement si le match est ajouté pour la première fois (ou retiré)
    if not match_previously_played and not inverse:
        # Si le match était non joué auparavant, incrémenter les matchs joués
        conn.execute('''
            UPDATE GroupStanding
            SET matches_played = matches_played + 1
            WHERE team_id = ?
        ''', (team1_id,))
        conn.execute('''
            UPDATE GroupStanding
            SET matches_played = matches_played + 1
            WHERE team_id = ?
        ''', (team2_id,))
    
    # Si on inverse (retire le match précédent), décrémenter les matchs joués
    elif inverse and match_previously_played:
        conn.execute('''
            UPDATE GroupStanding
            SET matches_played = matches_played - 1
            WHERE team_id = ?
        ''', (team1_id,))
        conn.execute('''
            UPDATE GroupStanding
            SET matches_played = matches_played - 1
            WHERE team_id = ?
        ''', (team2_id,))



if __name__ == '__main__':
    app.run(debug=False)
