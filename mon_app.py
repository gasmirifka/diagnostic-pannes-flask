from email.mime.multipart import MIMEMultipart
from flask import Flask, flash, request, jsonify, render_template, session, redirect, url_for, send_file
from functools import wraps
import sqlite3
import pandas as pd
import joblib
from datetime import time, timedelta, datetime, timezone
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
import os
import matplotlib.pyplot as plt
from xhtml2pdf import pisa
from translations import translations
from flask import g

app = Flask(__name__)
app.secret_key = 'cle_super_secrete'
app.permanent_session_lifetime = timedelta(minutes=1)
DB_PATH = "C:/Users/merci/OneDrive/Bureau/master/pannes.db"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}?timeout=30'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Traduction
@app.context_processor
def inject_translate():
    return dict(_=translate)

def translate(text):
    lang = session.get('lang', 'fr')
    return translations.get(text, {}).get(lang, text)

@app.route('/change_language/<lang>')
def change_language(lang):
    if lang not in ['fr', 'en', 'ja']:  # ajoute 'ja'
        lang = 'fr'
    session['lang'] = lang
    return redirect(request.referrer or url_for('home'))


# Gestion base de données

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=50)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA busy_timeout=50000")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Modèle et données

def charger_donnees():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM pannes", conn)
    conn.close()
    return df

def get_model():
    model = joblib.load("C:/Users/merci/OneDrive/Bureau/master/models/knn_model.pkl")
    vectorizer = joblib.load("C:/Users/merci/OneDrive/Bureau/master/models/vectorizer.pkl")
    return model, vectorizer

# Authentification et session

def log_connexion(username, panne=None, solution=None, action="connexion simple"):
    max_retries = 3
    retry_delay = 0.1
    for attempt in range(max_retries):
        try:
            db = get_db()
            db.execute("""
                INSERT INTO connexions (username, date_heure, panne, solution, action) 
                VALUES (?, ?, ?, ?, ?)
            """, (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), panne, solution, action))
            db.commit()
            break
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get('logged_in') or session.get('role') not in roles:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.before_request
def check_session_timeout():
    if 'logged_in' in session:
        now = datetime.now(timezone.utc)
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_dt = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
            if (now - last_activity_dt.replace(tzinfo=timezone.utc)) > timedelta(minutes=2):
                session.clear()
                return redirect(url_for('login'))
        session['last_activity'] = now.strftime('%Y-%m-%d %H:%M:%S')

# Routes principales

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and user['password'] == password:
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user['role']  # Stocke le rôle dans la session
            log_connexion(username, action="connexion")

            
            # Redirection en fonction du rôle
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'technicien':
                return redirect(url_for('diagnostic'))
            else:  # Opérateur
                return redirect(url_for('signalement_panne'))
        
        return "Identifiants incorrects"
    return render_template("login.html")
# Signalement pour opérateurs
@app.route('/signalement', methods=['GET', 'POST'])
@login_required
@role_required('operateur')
def signalement_panne():
    if request.method == 'POST':
        machine = request.form['machine']
        description = request.form['description']
        
        # Recherche de solution via le modèle IA
        fiche = chercher_fiche(description)
        
        db = get_db()
        db.execute("""
            INSERT INTO pannes (Panne, Solution, Catégorie, ID_Machine, Date, Operateur)
            VALUES (?, ?, ?, ?, ?, ?)
         """, (description, "À diagnostiquer", fiche['Catégorie'], 
         machine, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
         session['username']))
        log_connexion(session['username'], panne=description, action="signalement")

        db.commit()
        
                # Envoi d'email au technicien
        envoyer_alerte_mail({
            'Panne': description,
            'Solution': fiche['Solution'],
            'Catégorie': fiche['Catégorie'],
            'ID_Machine': machine,
            'Similarité': fiche['Similarité']
        })
        
        flash('Panne signalée avec succès! Un technicien a été notifié.', 'success')
        return redirect(url_for('signalement_panne'))
        
        flash('Panne signalée avec succès!', 'success')
        return redirect(url_for('signalement_panne'))
    
    return render_template('signalement_operateur.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session.get('role') == 'technicien':
        return redirect(url_for('diagnostic'))
    elif session.get('role') == 'operateur':
        return redirect(url_for('signalement_panne'))
    return redirect(url_for('login'))

@app.route('/liste_pannes')
@role_required('technicien')
def liste_pannes():
    try:
        conn = get_db()
        pannes = conn.execute("""
            SELECT Panne, Solution, Catégorie, ID_Machine, 
                   strftime('%Y-%m-%d %H:%M:%S', Date) as Date_formatted 
            FROM pannes 
            ORDER BY Date DESC
        """).fetchall()
        return render_template('liste_pannes.html', pannes=pannes)
    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
        return "Erreur lors de l'accès à la base de données", 500
@app.route('/diagnostic', methods=['GET', 'POST'])
@login_required
@role_required('technicien')
def diagnostic():
    # Récupérer les pannes non traitées
    db = get_db()
    pannes = db.execute("""
    SELECT * FROM pannes 
    WHERE Solution IS NULL OR trim(Solution) = '' OR lower(trim(Solution)) LIKE '%diagnostiquer%'
    ORDER BY Date DESC
""").fetchall()

    
    if request.method == 'POST':
        panne_id = request.form['panne_id']
        nouvelle_solution = request.form['solution']
        
        # Mettre à jour la solution
        db.execute("""
            UPDATE pannes SET Solution = ? 
            WHERE Panne = ?
        """, (nouvelle_solution, panne_id))
        # Enregistrer la connexion
        log_connexion(session['username'], panne=panne_id, solution=nouvelle_solution, action="diagnostic")
        db.commit()
        
        flash('Solution mise à jour avec succès!', 'success')
        return redirect(url_for('diagnostic'))
    
    return render_template('diagnostic_technicien.html', pannes=pannes)
    

@app.route('/admin')
@role_required('admin')
def admin_dashboard():
    conn = get_db()
    try:
        categories_data = conn.execute("""
            SELECT Catégorie, COUNT(*) as count 
            FROM pannes 
            GROUP BY Catégorie
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        chart_data = {
            'labels': [row['Catégorie'] for row in categories_data],
            'counts': [row['count'] for row in categories_data]
        }
        total_pannes = conn.execute("SELECT COUNT(*) FROM pannes").fetchone()[0]
        pannes_semaine = conn.execute("""
            SELECT COUNT(*) 
            FROM pannes 
            WHERE date(Date) >= date('now', 'weekday 0', '-7 days')
        """).fetchone()[0]
        connexions = conn.execute("""
            SELECT username, date_heure, panne 
            FROM connexions 
            WHERE username NOT IN ('admin', 'rifka')
            ORDER BY date_heure DESC 
            LIMIT 5
        """).fetchall()
        alertes = conn.execute("""
            SELECT Panne, COUNT(*) as count
            FROM pannes
            WHERE date(Date) >= date('now', 'weekday 0', '-7 days')
            GROUP BY Panne
            HAVING count >= 3
        """).fetchall()
        return render_template('admin.html', chart_data=chart_data,
                               stats={
                                   'total_pannes': total_pannes,
                                   'pannes_semaine': pannes_semaine,
                                   'alertes_count': len(alertes)
                               },
                               connexions=connexions,
                               alertes=alertes)
    except Exception as e:
        print(f"Erreur dans admin_dashboard: {str(e)}")
        return "Une erreur est survenue", 500

@app.route('/ajouter_panne', methods=['GET', 'POST'])
@role_required('technicien')
def ajouter_panne():
    if request.method == 'POST':
        panne = request.form['panne']
        solution = request.form['solution']
        categorie = request.form['categorie']
        id_machine = request.form['id_machine']
        db = get_db()
        db.execute("""
            INSERT INTO pannes (Panne, Solution, Catégorie, ID_Machine, Date)
            VALUES (?, ?, ?, ?, ?)""",
            (panne, solution, categorie, id_machine, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        return redirect(url_for('liste_pannes'))
    return render_template('ajouter_panne.html')

@app.route('/importer_csv', methods=['GET', 'POST'])
@role_required('admin')
def importer_csv():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            return redirect(request.url)
        file = request.files['file']
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            db = get_db()
            df.to_sql('pannes', db, if_exists='append', index=False)
            return redirect(url_for('liste_pannes'))
    return render_template('importer_csv.html')

@app.route('/generer_pdf')
@login_required
def generer_pdf():
    db = get_db()
    pannes = db.execute("SELECT * FROM pannes ORDER BY Date DESC").fetchall()
    html = render_template('rapport_pdf.html', pannes=pannes)
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', download_name='rapport_pannes.pdf')

# Fonctions métiers

def chercher_fiche(description):
    model, vectorizer = get_model()
    
    # Vectorisation de la nouvelle description
    print(f"\n=== Nouvelle requête ===")
    print(f"Description: {description}")
    vec = vectorizer.transform([description])
    
    # Recherche des plus proches voisins
    dist, indices = model.kneighbors(vec)
    
    # Affichage détaillé
    print("\n=== Résultats de similarité ===")
    print(f"Top résultat trouvé à distance: {dist[0][0]:.4f}")
    print(f"Similarité cosinus: {(1 - dist[0][0]) * 100:.2f}%")
    
    df = charger_donnees()
    fiche = df.iloc[indices[0][0]]
    
    print("\n=== Fiche trouvée ===")
    print(f"Description originale: {fiche['Panne']}")
    print(f"Solution associée: {fiche['Solution']}")
    
    return {
        'Panne': fiche['Panne'],
        'Solution': fiche['Solution'],
        'Catégorie': fiche.get('Catégorie', 'Inconnu'),
        'Code_Erreur': fiche.get('Erreur code', 'Inconnu'),
        'ID_Machine': fiche.get('ID_Machine', 'Inconnu'),
        'Similarité': f"{(1 - dist[0][0]) * 100:.2f}%"
    }

def enregistrer_diagnostic(description, fiche):
    db = get_db()
    db.execute("""
        INSERT INTO pannes (Panne, Solution, Catégorie, ID_Machine, Date)
        VALUES (?, ?, ?, ?, ?)""",
        (fiche["Panne"], fiche["Solution"], fiche["Catégorie"], fiche["ID_Machine"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()

def envoyer_alerte_mail(fiche, destinataire=None): 
    if not destinataire:
        destinataire = "gasmirifka5@gmail.com"
    
    expediteur = os.getenv('EMAIL_SENDER', 'gasmirifka5@gmail.com')
    mot_de_passe = os.getenv('EMAIL_PASSWORD', 'sxqz gxuy lomu jkdr')
    
    lang = session.get('lang', 'fr')
    
    def _(text):
        return translations.get(text, {}).get(lang, text)

    message = f"""
{_('🚨 Alerte de panne détectée !')}
{_('👤 Signalé par')} : {session.get('username', 'Un opérateur')}
{_('🏭 Machine')}     : {fiche['ID_Machine']}
{_('🔧 Panne')}       : {_(fiche['Panne'])}
{_('🛠 Solution')}    : {_(fiche['Solution'])}
{_('📁 Catégorie')}   : {_(fiche['Catégorie'])}
{_('🔎 Similarité')}  : {fiche['Similarité']}
"""

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(expediteur, mot_de_passe)
            msg = MIMEText(message, "plain", "utf-8")
            msg['Subject'] = f"{_('🚨 Alerte de panne')} - {fiche['ID_Machine']}"
            msg['From'] = expediteur
            msg['To'] = destinataire
            server.sendmail(expediteur, destinataire, msg.as_string())
    except Exception as e:
        app.logger.error(f"{_('Erreur lors de l\'envoi de l\'email :')} {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, threaded=True, use_reloader=False)

