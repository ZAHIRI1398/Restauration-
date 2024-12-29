import os
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import logging

app = Flask(__name__)
app.secret_key = 'votre_cle_secrète'

DB_PATH = 'C:/Users/adamy/OneDrive/Bureau/shared/reservations.db'

# Configuration de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def creer_tables():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Créer les tables si elles n'existent pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS menu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    description TEXT,
                    prix REAL NOT NULL,
                    categorie TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    personnes INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    heure TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations_plats (
                    reservation_id INTEGER NOT NULL,
                    plat_id INTEGER NOT NULL,
                    FOREIGN KEY (reservation_id) REFERENCES reservations(id),
                    FOREIGN KEY (plat_id) REFERENCES menu(id),
                    PRIMARY KEY (reservation_id, plat_id)
                )
            ''')

            conn.commit()
            print("Tables créées avec succès.")
    except sqlite3.Error as e:
        print(f"Erreur lors de la création des tables: {e}")

# Exécuter cette fonction pour créer les tables si nécessaire
creer_tables()

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/afficher_reservations')
def afficher_toutes_reservations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Récupérer toutes les réservations
        cursor.execute('SELECT * FROM reservations')
        reservations = cursor.fetchall()
        
        # Log des réservations récupérées
        app.logger.debug(f"Réservations récupérées : {reservations}")
        
        # Récupérer les plats réservés pour chaque réservation
        reservations_with_plats = []
        for reservation in reservations:
            cursor.execute('''
                SELECT menu.nom, menu.description, menu.prix 
                FROM reservations_plats
                JOIN menu ON reservations_plats.plat_id = menu.id
                WHERE reservations_plats.reservation_id = ?
            ''', (reservation[0],))
            plats = cursor.fetchall()

            # Log des plats récupérés
            app.logger.debug(f"Plats pour la réservation {reservation[0]} : {plats}")
            
            reservations_with_plats.append((reservation, plats))
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des réservations: {e}")
        reservations_with_plats = []

    conn.close()

    # Log pour vérifier les données passées au template
    app.logger.debug(f"Données passées au template : {reservations_with_plats}")
    
    return render_template('afficher_reservations.html', reservations_with_plats=reservations_with_plats)


@app.route('/reservations/<email>')
def afficher_reservations_par_email(email):
    db_path = DB_PATH
    
    # Lire les réservations pour un email spécifique
    reservations = lire_reservations_par_email(db_path, email)
    
    # Log pour vérifier les réservations récupérées
    app.logger.debug(f"Réservations récupérées pour {email}: {reservations}")
    
    return render_template('afficher_reservations.html', reservations=reservations, email=email)

def lire_reservations_par_email(db_path, email):
    """ Fonction qui récupère les réservations et les plats associés pour un email spécifique """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id, r.nom, r.personnes, r.date, r.heure, r.contact, r.email,
               GROUP_CONCAT(m.nom, ', ') AS plats_reserves
        FROM reservations AS r
        LEFT JOIN reservations_plats AS rp ON r.id = rp.reservation_id
        LEFT JOIN menu AS m ON rp.plat_id = m.id
        WHERE r.email = ?
        GROUP BY r.id
    ''', (email,))
    
    reservations = cursor.fetchall()
    
    # Log pour vérifier les résultats récupérés
    app.logger.debug(f"Réservations récupérées pour l'email {email} : {reservations}")

    conn.close()

    return reservations

# Au lieu de rd, utilisez rm -rf
rm -rf .git

# Puis continuez avec les autres commandes :
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ZAHIRI1398/Restauration-.git
git push -f origin main

@app.route('/supprimer_reservations', methods=['GET', 'POST'])
def supprimer_reservations():
    if request.method == 'POST':
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reservations')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erreur lors de la suppression des réservations : {e}")
        finally:
            conn.close()

        return redirect(url_for('afficher_toutes_reservations'))

    return render_template('supprimer_reservations.html')

def ajouter_reservation_avec_plats(reservation_id, plats):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Ajouter les plats réservés pour une réservation spécifique
        for plat_id in plats:  # plats est une liste d'IDs de plats
            cursor.execute('''
                INSERT INTO reservations_plats (reservation_id, plat_id)
                VALUES (?, ?)
            ''', (reservation_id, plat_id))
            app.logger.debug(f"Ajouté plat {plat_id} pour la réservation {reservation_id}")

        conn.commit()

@app.route('/ajouter_menu', methods=['GET']) 
def ajouter_menu():
    return render_template('ajouter-menu.html')

@app.route('/afficher_menu', methods=['GET'])
def afficher_menu():
    plats = lire_menu()
    return render_template('menu.html', plats=plats)

@app.route('/ajouter_plat', methods=['POST'])
def ajouter_plat():
    try:
        nom_plat = request.form.get('nom_plat')
        description = request.form.get('description')
        prix = request.form.get('prix')

        if not nom_plat or not description or not prix:
            flash("Tous les champs doivent être remplis.", "error")
            return redirect(url_for('ajouter_menu'))

        try:
            prix = float(prix)
        except ValueError:
            flash("Le prix doit être un nombre valide.", "error")
            return redirect(url_for('ajouter_menu'))

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO menu (nom, description, prix) VALUES (?, ?, ?)''', (nom_plat, description, prix))
            conn.commit()

        flash("Plat ajouté avec succès.", "success")

    except Exception as e:
        flash(f"Erreur lors de l'ajout du plat: {e}", "error")

    return redirect(url_for('afficher_menu'))

@app.route('/supprimer_plat/<int:plat_id>', methods=['POST'])
def supprimer_plat(plat_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM menu WHERE id = ?''', (plat_id,))
            conn.commit()

        flash("Plat supprimé avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression du plat: {e}", "error")

    return redirect(url_for('afficher_menu'))

def lire_menu():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM menu")
            plats = cursor.fetchall()
    except Exception as e:
        plats = []
        app.logger.error(f"Erreur lors de la lecture des plats: {e}")
    return plats

if __name__ == '__main__':
    app.run(debug=True)
