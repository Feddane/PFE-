from flask import render_template, request, redirect, url_for, session, flash, send_file, jsonify
from . import create_app, db
from .models import Reclamation, Admin, Superviseur, User
import os
from io import BytesIO
from .graph import generate_statistic_images
from datetime import date, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import grey


app = create_app()

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/select_role', methods=['POST'])
def select_role():
    role = request.form.get('role')
    if role == 'admin':
        return redirect(url_for('login_admin'))
    elif role == 'superviseur':
        return redirect(url_for('login_supervisor'))
        pass
    elif role == 'utilisateur':
        return redirect(url_for('login_user'))
    else:
        flash('Rôle non valide', 'error')
        return redirect(url_for('home'))

#all about SUPERVISOR
@app.route('/login_supervisor', methods=['GET', 'POST'])
def login_supervisor():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        supervisor = Superviseur.query.filter_by(username=username, password=password).first()
        if supervisor:
            session['username'] = username
            return redirect(url_for('reclamation_supervisor'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    return render_template('supervisor_dashboard.html')

@app.route('/reclamation_supervisor', methods=['GET', 'POST'])
def reclamation_supervisor():
    if 'username' not in session:
        return redirect(url_for('login_supervisor'))

    if request.method == 'POST':
        titre = request.form.get('titre')
        sites = request.form.get('sites')
        action_entreprise = request.form.get('action_entreprise')
        date_ouverture = request.form.get('date_ouverture')
        date_fin = request.form.get('date_fin')
        operateur = request.form.get('operateur')
        echeance = request.form.get('echeance')
        etages = request.form.get('etages')
        affecte_a = request.form.get('affecte_a')
        priorite = request.form.get('priorite')
        acces = request.form.get('acces')
        ouvert_par = request.form.get('ouvert_par')
        description = request.form.get('description')
        status = request.form.get('status')
        categorie = request.form.get('categorie')
        famille = request.form.get('famille')
        commentaire = request.form.get('commentaire')
        fichier = request.files.get('fileUpload')

        fichier_nom = None

        if fichier:
            fichier_nom = fichier.filename

        nouvelle_reclamation = Reclamation(
            titre=titre,
            sites=sites,
            action_entreprise=action_entreprise,
            date_ouverture=date_ouverture,
            date_fin=date_fin,
            operateur=operateur,
            echeance=echeance,
            etages=etages,
            affecte_a=affecte_a,
            priorite=priorite,
            acces=acces,
            ouvert_par=ouvert_par,
            description=description,
            status=status,
            categorie=categorie,
            famille=famille,
            commentaire=commentaire,
            fichier=fichier_nom,
            role='superviseur'
        )

        db.session.add(nouvelle_reclamation)
        db.session.commit()

        return redirect(url_for('reclamation_supervisor'))

    return render_template('reclamation_supervisor.html')

@app.route('/historique_supervisor', methods=['GET'])
def historique_supervisor():
    if 'username' not in session:
        return redirect(url_for('login_supervisor'))

    categorie = request.args.get('categorie')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    status = request.args.get('status')

    query = Reclamation.query

    if categorie:
        query = query.filter(Reclamation.categorie.ilike(f"%{categorie}%"))
    if date_debut and date_fin:
        query = query.filter(Reclamation.date_ouverture.between(date_debut, date_fin))
    if status:
        query = query.filter(Reclamation.status.ilike(f"%{status}%"))

    query = query.order_by(Reclamation.id)

    results = query.all()

    return render_template('historique_supervisor.html', results=results)


@app.route('/statistique/data', methods=['GET'])
def statistique_data():
    if 'username' not in session:
        return redirect(url_for('login_supervisor'))

    mois = request.args.get('mois')
    categorie = request.args.get('categorie')

    images, error = generate_statistic_images(mois, categorie)
    if error:
        return error, 400

    return jsonify(images)


@app.route('/statistique', methods=['GET'])
def statistique():
    if 'username' not in session:
        return redirect(url_for('login_supervisor'))

    mois = request.args.get('mois')
    categorie = request.args.get('categorie')
    print("categorie", categorie)

    operateur_file_path = os.path.join(app.static_folder, 'operateur.txt')
    try:
        with open(operateur_file_path, 'r', encoding='utf-8') as file:
            operateur_list = file.read().strip().split('\n')
    except FileNotFoundError:
        operateur_list = []

    actifs_count = len(set(operateur_list))

    images, error = generate_statistic_images(mois, categorie)
    if error:
        return error, 400

    incidents_count = Reclamation.query.count()
    categories_count = 10
    reclamations = Reclamation.query.order_by(Reclamation.id).all()

    return render_template('statistique.html', actifs_count=actifs_count, incidents_count=incidents_count,
                           categories_count=categories_count, reclamations=reclamations, **images)





#all about USER
@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(username=username, first_name=first_name, last_name=last_name, email=email, password=password).first()

        if user:

            session['username'] = user.first_name
            return redirect(url_for('reclamation_user'))
        else:
            flash('Coordonnées Incorrectes!', 'danger')

    return render_template('user_dashboard.html')


@app.route('/reclamation_user', methods=['GET', 'POST'])
def reclamation_user():
    if 'username' not in session:
        return redirect(url_for('login_user'))

    if request.method == 'POST':
        titre = request.form.get('titre')
        sites = request.form.get('sites')
        action_entreprise = request.form.get('action_entreprise')
        date_ouverture = request.form.get('date_ouverture')
        date_fin = request.form.get('date_fin')
        operateur = request.form.get('operateur')
        echeance = request.form.get('echeance')
        etages = request.form.get('etages')
        affecte_a = request.form.get('affecte_a')
        priorite = request.form.get('priorite')
        acces = request.form.get('acces')
        ouvert_par = request.form.get('ouvert_par')
        description = request.form.get('description')
        status = request.form.get('status')
        categorie = request.form.get('categorie')
        famille = request.form.get('famille')
        commentaire = request.form.get('commentaire')
        fichier = request.files.get('fileUpload')

        fichier_nom = None

        if fichier:
            fichier_nom = fichier.filename

        nouvelle_reclamation = Reclamation(
            titre=titre,
            sites=sites,
            action_entreprise=action_entreprise,
            date_ouverture=date_ouverture,
            date_fin=date_fin,
            operateur=operateur,
            echeance=echeance,
            etages=etages,
            affecte_a=affecte_a,
            priorite=priorite,
            acces=acces,
            ouvert_par=ouvert_par,
            description=description,
            status=status,
            categorie=categorie,
            famille=famille,
            commentaire=commentaire,
            fichier=fichier_nom,
            role='user'
        )

        db.session.add(nouvelle_reclamation)
        db.session.commit()

        return redirect(url_for('reclamation_user'))

    return render_template('reclamation_user.html')


@app.route('/historique_user', methods=['GET'])
def historique_user():
    if 'username' not in session:
        return redirect(url_for('login_user'))

    categorie = request.args.get('categorie')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    status = request.args.get('status')

    query = Reclamation.query.filter_by(role='user')

    if categorie:
        query = query.filter(Reclamation.categorie.ilike(f"%{categorie}%"))
    if date_debut and date_fin:
        query = query.filter(Reclamation.date_ouverture.between(date_debut, date_fin))
    if status:
        query = query.filter(Reclamation.status.ilike(f"%{status}%"))

    query = query.order_by(Reclamation.id)

    results = query.all()

    return render_template('historique_user.html', results=results)

@app.route('/all_reclamations_user', methods=['GET'])
def all_reclamations_user():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    reclamations = Reclamation.query.filter_by(role='user').order_by(Reclamation.id).all()
    results = [{
        'id': r.id,
        'titre': r.titre,
        'sites': r.sites,
        'action_entreprise': r.action_entreprise,
        'date_ouverture': r.date_ouverture.strftime('%Y-%m-%d'),
        'date_fin': r.date_fin.strftime('%Y-%m-%d'),
        'operateur': r.operateur,
        'echeance': r.echeance.strftime('%Y-%m-%d'),
        'etages': r.etages,
        'affecte_a': r.affecte_a,
        'priorite': r.priorite,
        'acces': r.acces,
        'ouvert_par': r.ouvert_par,
        'description': r.description,
        'status': r.status,
        'categorie': r.categorie,
        'famille': r.famille,
        'commentaire': r.commentaire,
        'fichier': r.fichier
    } for r in reclamations]
    return jsonify(results)



#all about ADMIN
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Admin.query.filter_by(username=username, password=password).first()

        if user:
            session['username'] = username
            return redirect(url_for('reclamation'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')

    return render_template('admin_dashboard.html')

@app.route('/changer_mdp', methods=['GET', 'POST'])
def changer_mdp():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        username = session.get('username')

        if username:
            user = Admin.query.filter_by(username=username, password=old_password).first()

            if user:
                user.password = new_password
                db.session.commit()
                flash('Mot de passe changé avec succès', 'success')
                return redirect(url_for('login_admin'))
            else:
                flash('Ancien mot de passe incorrect', 'error')
        else:
            flash('Vous devez être connecté pour changer de mot de passe', 'error')

    return render_template('changer_mdp.html')

@app.route('/reclamation', methods=['GET', 'POST'])
def reclamation():
    if 'username' not in session:
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        titre = request.form.get('titre')
        sites = request.form.get('sites')
        action_entreprise = request.form.get('action_entreprise')
        date_ouverture = request.form.get('date_ouverture')
        date_fin = request.form.get('date_fin')
        operateur = request.form.get('operateur')
        echeance = request.form.get('echeance')
        etages = request.form.get('etages')
        affecte_a = request.form.get('affecte_a')
        priorite = request.form.get('priorite')
        acces = request.form.get('acces')
        ouvert_par = request.form.get('ouvert_par')
        description = request.form.get('description')
        status = request.form.get('status')
        categorie = request.form.get('categorie')
        famille = request.form.get('famille')
        commentaire = request.form.get('commentaire')
        fichier = request.files.get('fileUpload')

        fichier_nom = None

        if fichier:
            fichier_nom = fichier.filename

        nouvelle_reclamation = Reclamation(
            titre=titre,
            sites=sites,
            action_entreprise=action_entreprise,
            date_ouverture=date_ouverture,
            date_fin=date_fin,
            operateur=operateur,
            echeance=echeance,
            etages=etages,
            affecte_a=affecte_a,
            priorite=priorite,
            acces=acces,
            ouvert_par=ouvert_par,
            description=description,
            status=status,
            categorie=categorie,
            famille=famille,
            commentaire=commentaire,
            fichier=fichier_nom,
            role='admin'
        )

        db.session.add(nouvelle_reclamation)
        db.session.commit()

        return redirect(url_for('reclamation'))

    return render_template('reclamation.html')

@app.route('/historique', methods=['GET'])
def historique():
    if 'username' not in session:
        return redirect(url_for('login_admin'))

    categorie = request.args.get('categorie')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    status = request.args.get('status')

    query = Reclamation.query

    if categorie:
        query = query.filter(Reclamation.categorie.ilike(f"%{categorie}%"))
    if date_debut and date_fin:
        query = query.filter(Reclamation.date_ouverture.between(date_debut, date_fin))
    if status:
        query = query.filter(Reclamation.status.ilike(f"%{status}%"))

    query = query.order_by(Reclamation.id)

    results = query.all()

    return render_template('historique.html', results=results)


@app.route('/update_status', methods=['POST'])
def update_status():
    if 'username' not in session:
        return redirect(url_for('login'))

    record_id = request.form.get('recordId')
    new_status = request.form.get('newStatus')
    current_status = request.form.get('currentStatus')

    if record_id and new_status and current_status:
        current_status_lower = current_status.lower()
        new_status_lower = new_status.lower()
        if not (current_status_lower == 'inactif' and new_status_lower == 'actif'):

           
            reclamation = Reclamation.query.get(record_id)
            reclamation.status = new_status
            db.session.commit()
            flash('Statut mis à jour avec succès', 'success')
        else:
            flash('Impossible de changer le statut de Inactif à Actif.', 'error')


    if 'historique_user' in request.referrer:
        return redirect(url_for('historique_user'))
    else:
        return redirect(url_for('historique'))

@app.route('/update_date_fin', methods=['POST'])
def update_date_fin():
    if 'username' not in session:
        return redirect(url_for('login'))

    record_id = request.form.get('recordId')
    new_date_fin = request.form.get('newDateFin')

    if record_id and new_date_fin:

       
        reclamation = Reclamation.query.get(record_id)
        reclamation.date_fin = new_date_fin
        db.session.commit()
        flash('Date de fin mise à jour avec succès', 'success')


    if 'historique_user' in request.referrer:
        return redirect(url_for('historique_user'))
    else:
        return redirect(url_for('historique'))


@app.route('/export', methods=['GET'])
def export():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    today = date.today()
    reclamations = Reclamation.query.filter_by(date_ouverture=today).all()

    if not reclamations:
        flash("Il n'y a pas de réclamations à exporter pour aujourd'hui.", "warning")
        return redirect(url_for('home'))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    def space_available(space_needed):
        nonlocal y
        return y - space_needed > 40

    c.setFont("Times-Roman", 13)
    c.drawString(width - 150, y, f"Date : {today.strftime('%Y-%m-%d')}")
    y -= 26

    c.setFont("Times-Bold", 18)
    c.setFillColor(grey)
    c.drawString(30, y, "Requêtes enregistrées")
    c.setLineWidth(5)
    y -= 40

    c.setFillColor('black')
    c.setFont("Times-Roman", 14)

    for index, reclamation in enumerate(reclamations):
        if not space_available(200):
            c.showPage()
            c.setFont("Times-Roman", 14)
            y = height - 40

        c.setStrokeColor('red')
        c.setLineWidth(5)
        c.line(30, y + 15, width - 30, y + 15)

        c.setFont("Times-Bold", 16)
        c.setFillColor('red')
        c.drawString(30, y, f"Requête N° : {reclamation.id}")
        c.setFillColor('black')
        c.setFont("Times-Roman", 14)
        y -= 45

        fields = [
            (f"Titre : {reclamation.titre}", 15),
            (f"Status : {reclamation.status}", 15),
            (f"Priorité : {reclamation.priorite}", 15),
            (f"Categorie : {reclamation.categorie}", 15),
            (f"Ouvert par : {reclamation.ouvert_par}", 15),
            (f"Affecté à : {reclamation.affecte_a}", 15),
            (f"Échéance : {reclamation.echeance}", 15),
            (f"Opérateur : {reclamation.operateur}", 30),
            ("Description:", 15),
            (f"{reclamation.description}", 15),
            ("" , 30)
        ]
        
        for field, space_needed in fields:
            if not space_available(space_needed):
                c.showPage()
                c.setFont("Times-Roman", 14)
                y = height - 40
            if field == "Description:":
                c.setFont("Times-Bold", 14)
                c.setFillColor(grey)
            c.drawString(30, y, field)
            if field == "Description:":
                c.setFont("Times-Roman", 14)
                c.setFillColor('black')
            y -= space_needed

        if index < len(reclamations) - 1:
            y -= 20

    c.setStrokeColor('red')
    c.setLineWidth(5)
    c.line(30, y - 10, width - 30, y - 10)

    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.setFont("Times-Bold", 14)
    c.drawRightString(width - 30, 40, f"Généré le : {generated_at}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='BRQ.pdf', mimetype='application/pdf')
    

@app.route('/all_reclamations', methods=['GET'])
def all_reclamations():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    reclamations = Reclamation.query.order_by(Reclamation.id).all()
    results = [{
        'id': r.id,
        'titre': r.titre,
        'sites': r.sites,
        'action_entreprise': r.action_entreprise,
        'date_ouverture': r.date_ouverture.strftime('%Y-%m-%d'),
        'date_fin': r.date_fin.strftime('%Y-%m-%d'),
        'operateur': r.operateur,
        'echeance': r.echeance.strftime('%Y-%m-%d'),
        'etages': r.etages,
        'affecte_a': r.affecte_a,
        'priorite': r.priorite,
        'acces': r.acces,
        'ouvert_par': r.ouvert_par,
        'description': r.description,
        'status': r.status,
        'categorie': r.categorie,
        'famille': r.famille,
        'commentaire': r.commentaire,
        'fichier': r.fichier
    } for r in reclamations]
    return jsonify(results)


@app.route('/creer_user', methods=['GET', 'POST'])
def creer_user():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']


        new_user = User(username=username, first_name=first_name, last_name=last_name, email=email, password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Utilisateur créé avec succès!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erreur! Veuillez réessayer.', 'danger')

        return redirect(url_for('creer_user'))

    return render_template('creer_user.html')


@app.route('/creer_superviseur', methods=['GET', 'POST'])
def creer_superviseur():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = Superviseur(username=username, password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Superviseur créé avec succès!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de la création de superviseur. Veuillez réessayer.', 'danger')

        return redirect(url_for('creer_superviseur'))

    return render_template('creer_superviseur.html')

@app.route('/creer_admin', methods=['GET', 'POST'])
def creer_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = Admin(username=username, password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Administrateur créé avec succès!', 'success')
        except Exception as e:
            db.session.rollback()
            flash("Erreur lors de la création de l'administrateur. Veuillez réessayer.", 'danger')

        return redirect(url_for('creer_admin'))

    return render_template('creer_admin.html')

@app.route('/supprimer', methods=['GET', 'POST'])
def supprimer():
    if request.method == 'POST':
        if 'username' not in session:
            flash('Vous devez être connecté pour effectuer cette action.', 'error')
            return redirect(url_for('login'))

        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'admin':
            utilisateur = Admin.query.filter_by(username=username).first()
        elif role == 'superviseur':
            utilisateur = Superviseur.query.filter_by(username=username).first()
        elif role == 'utilisateur':
            utilisateur = User.query.filter_by(username=username).first()
        else:
            flash('Rôle d\'utilisateur non valide.', 'error')
            return redirect(url_for('supprimer'))

        if utilisateur:
            db.session.delete(utilisateur)
            db.session.commit()
            flash(f'{role.capitalize()} supprimé avec succès.', 'success')
        else:
            flash('Nom d\'utilisateur incorrect.', 'error')

        return redirect(url_for('supprimer'))

    return render_template('supprimer.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))