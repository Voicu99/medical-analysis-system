"""
Sistem Management Analize Medicale
Aplicație Flask pentru gestionarea pacienților și analizelor medicale

Autor: Librimir Voicu
Data: 15.07.2025
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import logging
from typing import Dict, List, Optional
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
import io

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('medical_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurare aplicație Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'medical-analysis-system-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_analysis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Asigurăm că folderul uploads există
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# Modele de date
class Patient(db.Model):
    """
    Model pentru pacienți
    
    Attributes:
        id (int): Identificator unic
        nume (str): Numele pacientului
        prenume (str): Prenumele pacientului
        cnp (str): Codul numeric personal
        varsta (int): Vârsta pacientului
        sex (str): Sexul pacientului (M/F)
        telefon (str): Numărul de telefon
        adresa (str): Adresa pacientului
        created_at (datetime): Data creării înregistrării
    """
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(100), nullable=False, index=True)
    prenume = db.Column(db.String(100), nullable=False, index=True)
    cnp = db.Column(db.String(13), unique=True, nullable=False, index=True)
    varsta = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(1), nullable=False)  # M/F
    telefon = db.Column(db.String(20))
    adresa = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relație cu analizele
    analyses = db.relationship('Analysis', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<Patient {self.nume} {self.prenume}>'
    
    def to_dict(self) -> Dict:
        """Convertește obiectul în dicționar pentru JSON"""
        return {
            'id': self.id,
            'nume': self.nume,
            'prenume': self.prenume,
            'cnp': self.cnp,
            'varsta': self.varsta,
            'sex': self.sex,
            'telefon': self.telefon,
            'adresa': self.adresa,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_analyses': len(self.analyses)
        }

class Analysis(db.Model):
    """
    Model pentru analize medicale
    
    Attributes:
        id (int): Identificator unic
        patient_id (int): ID-ul pacientului
        tip_analiza (str): Tipul analizei
        rezultat (str): Rezultatul analizei
        valori_normale (str): Valorile normale de referință
        observatii (str): Observații medicale
        data_recoltare (date): Data recoltării
        data_rezultat (date): Data rezultatului
        medic (str): Numele medicului
        laborator (str): Numele laboratorului
        created_at (datetime): Data creării înregistrării
    """
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    tip_analiza = db.Column(db.String(200), nullable=False, index=True)
    rezultat = db.Column(db.Text, nullable=False)
    valori_normale = db.Column(db.String(100))
    observatii = db.Column(db.Text)
    data_recoltare = db.Column(db.Date, nullable=False, index=True)
    data_rezultat = db.Column(db.Date, nullable=False, index=True)
    medic = db.Column(db.String(100))
    laborator = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self) -> str:
        return f'<Analysis {self.tip_analiza} - {self.patient.nume}>'
    
    def to_dict(self) -> Dict:
        """Convertește obiectul în dicționar pentru JSON"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.nume} {self.patient.prenume}",
            'tip_analiza': self.tip_analiza,
            'rezultat': self.rezultat,
            'valori_normale': self.valori_normale,
            'observatii': self.observatii,
            'data_recoltare': self.data_recoltare.isoformat() if self.data_recoltare else None,
            'data_rezultat': self.data_rezultat.isoformat() if self.data_rezultat else None,
            'medic': self.medic,
            'laborator': self.laborator,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Funcții utilitare
def validate_cnp(cnp: str) -> bool:
    """Validează CNP-ul românesc"""
    if len(cnp) != 13 or not cnp.isdigit():
        return False
    
    # Validare algoritmică simplă
    control_digits = "279146358279"
    control_sum = sum(int(cnp[i]) * int(control_digits[i]) for i in range(12))
    control_digit = control_sum % 11
    
    if control_digit == 10:
        control_digit = 1
    
    return control_digit == int(cnp[12])

def get_statistics() -> Dict:
    """Obține statistici generale ale sistemului"""
    total_patients = Patient.query.count()
    total_analyses = Analysis.query.count()
    
    # Analize din ultimele 30 de zile
    from datetime import timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_analyses = Analysis.query.filter(
        Analysis.created_at >= thirty_days_ago
    ).count()
    
    # Distribuție pe sex
    male_patients = Patient.query.filter_by(sex='M').count()
    female_patients = Patient.query.filter_by(sex='F').count()
    
    return {
        'total_patients': total_patients,
        'total_analyses': total_analyses,
        'recent_analyses': recent_analyses,
        'male_patients': male_patients,
        'female_patients': female_patients
    }

# Rute principale
@app.route('/')
def index():
    """Pagina principală cu dashboard"""
    logger.info("Accesare pagina principală")
    
    stats = get_statistics()
    recent_analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_patients=stats['total_patients'],
                         total_analyses=stats['total_analyses'],
                         recent_analyses=recent_analyses,
                         stats=stats)

# CRUD PACIENȚI
@app.route('/patients')
def patients_list():
    """Lista pacienți cu opțiuni de filtrare și sortare"""
    logger.info("Accesare lista pacienți")
    
    # Parametri de filtrare și sortare
    search = request.args.get('search', '').strip()
    sex_filter = request.args.get('sex', '')
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    sort_by = request.args.get('sort', 'nume')
    order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Query de bază
    query = Patient.query
    
    # Filtrare după nume/prenume/CNP
    if search:
        query = query.filter(
            (Patient.nume.ilike(f'%{search}%')) | 
            (Patient.prenume.ilike(f'%{search}%')) |
            (Patient.cnp.ilike(f'%{search}%'))
        )
    
    # Filtrare după sex
    if sex_filter and sex_filter in ['M', 'F']:
        query = query.filter(Patient.sex == sex_filter)
    
    # Filtrare după vârstă
    if age_min is not None:
        query = query.filter(Patient.varsta >= age_min)
    if age_max is not None:
        query = query.filter(Patient.varsta <= age_max)
    
    # Sortare
    if sort_by == 'nume':
        query = query.order_by(Patient.nume.asc() if order == 'asc' else Patient.nume.desc())
    elif sort_by == 'varsta':
        query = query.order_by(Patient.varsta.asc() if order == 'asc' else Patient.varsta.desc())
    elif sort_by == 'created_at':
        query = query.order_by(Patient.created_at.asc() if order == 'asc' else Patient.created_at.desc())
    
    # Paginare
    patients = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('patients/list.html', 
                         patients=patients,
                         search=search,
                         sex_filter=sex_filter,
                         age_min=age_min,
                         age_max=age_max,
                         sort_by=sort_by,
                         order=order)

@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
    """Adăugare pacient nou"""
    if request.method == 'POST':
        try:
            # Validare CNP
            cnp = request.form['cnp'].strip()
            if not validate_cnp(cnp):
                flash('CNP invalid!', 'error')
                return render_template('patients/add.html')
            
            # Verificare unicitate CNP
            existing_patient = Patient.query.filter_by(cnp=cnp).first()
            if existing_patient:
                flash('Există deja un pacient cu acest CNP!', 'error')
                return render_template('patients/add.html')
            
            patient = Patient(
                nume=request.form['nume'].strip().title(),
                prenume=request.form['prenume'].strip().title(),
                cnp=cnp,
                varsta=int(request.form['varsta']),
                sex=request.form['sex'],
                telefon=request.form.get('telefon', '').strip(),
                adresa=request.form.get('adresa', '').strip()
            )
            
            db.session.add(patient)
            db.session.commit()
            
            logger.info(f"Pacient adăugat: {patient.nume} {patient.prenume} (CNP: {patient.cnp})")
            flash('Pacient adăugat cu succes!', 'success')
            return redirect(url_for('patients_list'))
            
        except ValueError:
            flash('Vârsta trebuie să fie un număr valid!', 'error')
        except Exception as e:
            logger.error(f"Eroare la adăugarea pacientului: {str(e)}")
            flash('Eroare la adăugarea pacientului!', 'error')
            db.session.rollback()
    
    return render_template('patients/add.html')

@app.route('/patients/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id: int):
    """Editare pacient"""
    patient = Patient.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validare CNP
            cnp = request.form['cnp'].strip()
            if not validate_cnp(cnp):
                flash('CNP invalid!', 'error')
                return render_template('patients/edit.html', patient=patient)
            
            # Verificare unicitate CNP (excluding current patient)
            existing_patient = Patient.query.filter(
                Patient.cnp == cnp,
                Patient.id != id
            ).first()
            if existing_patient:
                flash('Există deja un pacient cu acest CNP!', 'error')
                return render_template('patients/edit.html', patient=patient)
            
            patient.nume = request.form['nume'].strip().title()
            patient.prenume = request.form['prenume'].strip().title()
            patient.cnp = cnp
            patient.varsta = int(request.form['varsta'])
            patient.sex = request.form['sex']
            patient.telefon = request.form.get('telefon', '').strip()
            patient.adresa = request.form.get('adresa', '').strip()
            
            db.session.commit()
            
            logger.info(f"Pacient editat: {patient.nume} {patient.prenume} (ID: {patient.id})")
            flash('Pacient actualizat cu succes!', 'success')
            return redirect(url_for('patients_list'))
            
        except ValueError:
            flash('Vârsta trebuie să fie un număr valid!', 'error')
        except Exception as e:
            logger.error(f"Eroare la editarea pacientului: {str(e)}")
            flash('Eroare la actualizarea pacientului!', 'error')
            db.session.rollback()
    
    return render_template('patients/edit.html', patient=patient)

@app.route('/patients/delete/<int:id>')
def delete_patient(id: int):
    """Ștergere pacient"""
    try:
        patient = Patient.query.get_or_404(id)
        nume_complet = f"{patient.nume} {patient.prenume}"
        
        db.session.delete(patient)
        db.session.commit()
        
        logger.info(f"Pacient șters: {nume_complet} (ID: {id})")
        flash('Pacient șters cu succes!', 'success')
        
    except Exception as e:
        logger.error(f"Eroare la ștergerea pacientului: {str(e)}")
        flash('Eroare la ștergerea pacientului!', 'error')
        db.session.rollback()
    
    return redirect(url_for('patients_list'))

@app.route('/patients/view/<int:id>')
def view_patient(id: int):
    """Vizualizare detalii pacient"""
    patient = Patient.query.get_or_404(id)
    analyses = Analysis.query.filter_by(patient_id=id).order_by(Analysis.data_rezultat.desc()).all()
    
    return render_template('patients/view.html', patient=patient, analyses=analyses)

# CRUD ANALIZE
@app.route('/analyses')
def analyses_list():
    """Lista analize cu opțiuni de filtrare și sortare"""
    logger.info("Accesare lista analize")
    
    # Parametri de filtrare și sortare
    patient_id = request.args.get('patient_id', type=int)
    tip_analiza = request.args.get('tip_analiza', '').strip()
    medic = request.args.get('medic', '').strip()
    laborator = request.args.get('laborator', '').strip()
    data_start = request.args.get('data_start')
    data_end = request.args.get('data_end')
    sort_by = request.args.get('sort', 'data_rezultat')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Query de bază
    query = Analysis.query
    
    # Filtrare după pacient
    if patient_id:
        query = query.filter(Analysis.patient_id == patient_id)
    
    # Filtrare după tip analiză
    if tip_analiza:
        query = query.filter(Analysis.tip_analiza.ilike(f'%{tip_analiza}%'))
    
    # Filtrare după medic
    if medic:
        query = query.filter(Analysis.medic.ilike(f'%{medic}%'))
    
    # Filtrare după laborator
    if laborator:
        query = query.filter(Analysis.laborator.ilike(f'%{laborator}%'))
    
    # Filtrare după interval de date
    if data_start:
        try:
            start_date = datetime.strptime(data_start, '%Y-%m-%d').date()
            query = query.filter(Analysis.data_rezultat >= start_date)
        except ValueError:
            flash('Format dată incorect pentru data de început!', 'error')
    
    if data_end:
        try:
            end_date = datetime.strptime(data_end, '%Y-%m-%d').date()
            query = query.filter(Analysis.data_rezultat <= end_date)
        except ValueError:
            flash('Format dată incorect pentru data de sfârșit!', 'error')
    
    # Sortare
    if sort_by == 'data_rezultat':
        query = query.order_by(Analysis.data_rezultat.asc() if order == 'asc' else Analysis.data_rezultat.desc())
    elif sort_by == 'tip_analiza':
        query = query.order_by(Analysis.tip_analiza.asc() if order == 'asc' else Analysis.tip_analiza.desc())
    elif sort_by == 'patient':
        query = query.join(Patient).order_by(Patient.nume.asc() if order == 'asc' else Patient.nume.desc())
    elif sort_by == 'medic':
        query = query.order_by(Analysis.medic.asc() if order == 'asc' else Analysis.medic.desc())
    elif sort_by == 'created_at':
        query = query.order_by(Analysis.created_at.asc() if order == 'asc' else Analysis.created_at.desc())
    
    # Paginare
    analyses = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    patients = Patient.query.order_by(Patient.nume).all()
    
    return render_template('analyses/list.html', 
                         analyses=analyses,
                         patients=patients,
                         patient_id=patient_id,
                         tip_analiza=tip_analiza,
                         medic=medic,
                         laborator=laborator,
                         data_start=data_start,
                         data_end=data_end,
                         sort_by=sort_by,
                         order=order)

@app.route('/analyses/add', methods=['GET', 'POST'])
def add_analysis():
    """Adăugare analiză nouă"""
    if request.method == 'POST':
        try:
            # Validare date
            data_recoltare = datetime.strptime(request.form['data_recoltare'], '%Y-%m-%d').date()
            data_rezultat = datetime.strptime(request.form['data_rezultat'], '%Y-%m-%d').date()
            
            if data_rezultat < data_recoltare:
                flash('Data rezultatului nu poate fi anterioară datei recoltării!', 'error')
                patients = Patient.query.order_by(Patient.nume).all()
                return render_template('analyses/add.html', patients=patients)
            
            analysis = Analysis(
                patient_id=int(request.form['patient_id']),
                tip_analiza=request.form['tip_analiza'].strip(),
                rezultat=request.form['rezultat'].strip(),
                valori_normale=request.form.get('valori_normale', '').strip(),
                observatii=request.form.get('observatii', '').strip(),
                data_recoltare=data_recoltare,
                data_rezultat=data_rezultat,
                medic=request.form.get('medic', '').strip(),
                laborator=request.form.get('laborator', '').strip()
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            logger.info(f"Analiză adăugată: {analysis.tip_analiza} pentru pacientul {analysis.patient.nume} {analysis.patient.prenume}")
            flash('Analiză adăugată cu succes!', 'success')
            return redirect(url_for('analyses_list'))
            
        except ValueError as e:
            flash('Format dată incorect!', 'error')
        except Exception as e:
            logger.error(f"Eroare la adăugarea analizei: {str(e)}")
            flash('Eroare la adăugarea analizei!', 'error')
            db.session.rollback()
    
    patients = Patient.query.order_by(Patient.nume).all()
    return render_template('analyses/add.html', patients=patients)

@app.route('/analyses/edit/<int:id>', methods=['GET', 'POST'])
def edit_analysis(id: int):
    """Editare analiză"""
    analysis = Analysis.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validare date
            data_recoltare = datetime.strptime(request.form['data_recoltare'], '%Y-%m-%d').date()
            data_rezultat = datetime.strptime(request.form['data_rezultat'], '%Y-%m-%d').date()
            
            if data_rezultat < data_recoltare:
                flash('Data rezultatului nu poate fi anterioară datei recoltării!', 'error')
                patients = Patient.query.order_by(Patient.nume).all()
                return render_template('analyses/edit.html', analysis=analysis, patients=patients)
            
            analysis.patient_id = int(request.form['patient_id'])
            analysis.tip_analiza = request.form['tip_analiza'].strip()
            analysis.rezultat = request.form['rezultat'].strip()
            analysis.valori_normale = request.form.get('valori_normale', '').strip()
            analysis.observatii = request.form.get('observatii', '').strip()
            analysis.data_recoltare = data_recoltare
            analysis.data_rezultat = data_rezultat
            analysis.medic = request.form.get('medic', '').strip()
            analysis.laborator = request.form.get('laborator', '').strip()
            
            db.session.commit()
            
            logger.info(f"Analiză editată: {analysis.tip_analiza} (ID: {analysis.id})")
            flash('Analiză actualizată cu succes!', 'success')
            return redirect(url_for('analyses_list'))
            
        except ValueError:
            flash('Format dată incorect!', 'error')
        except Exception as e:
            logger.error(f"Eroare la editarea analizei: {str(e)}")
            flash('Eroare la actualizarea analizei!', 'error')
            db.session.rollback()
    
    patients = Patient.query.order_by(Patient.nume).all()
    return render_template('analyses/edit.html', analysis=analysis, patients=patients)

@app.route('/analyses/delete/<int:id>')
def delete_analysis(id: int):
    """Ștergere analiză"""
    try:
        analysis = Analysis.query.get_or_404(id)
        tip_analiza = analysis.tip_analiza
        
        db.session.delete(analysis)
        db.session.commit()
        
        logger.info(f"Analiză ștearsă: {tip_analiza} (ID: {id})")
        flash('Analiză ștearsă cu succes!', 'success')
        
    except Exception as e:
        logger.error(f"Eroare la ștergerea analizei: {str(e)}")
        flash('Eroare la ștergerea analizei!', 'error')
        db.session.rollback()
    
    return redirect(url_for('analyses_list'))

@app.route('/analyses/view/<int:id>')
def view_analysis(id: int):
    """Vizualizare detalii analiză"""
    analysis = Analysis.query.get_or_404(id)
    return render_template('analyses/view.html', analysis=analysis)

# GENERARE RAPOARTE
@app.route('/reports/analysis/<int:analysis_id>')
def generate_analysis_report(analysis_id: int):
    """Generare raport pentru o analiză"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    return render_template('reports/analysis_report.html', 
                         analysis=analysis,
                         patient=analysis.patient)

@app.route('/reports/patient/<int:patient_id>')
def generate_patient_report(patient_id: int):
    """Generare raport complet pentru un pacient"""
    patient = Patient.query.get_or_404(patient_id)
    analyses = Analysis.query.filter_by(patient_id=patient_id).order_by(Analysis.data_rezultat.desc()).all()
    
    return render_template('reports/patient_report.html', 
                         patient=patient,
                         analyses=analyses)

@app.route('/reports/statistics')
def statistics_report():
    """Raport statistici generale"""
    stats = get_statistics()
    
    # Analize pe tip
    from sqlalchemy import func
    analyses_by_type = db.session.query(
        Analysis.tip_analiza,
        func.count(Analysis.id).label('count')
    ).group_by(Analysis.tip_analiza).order_by(func.count(Analysis.id).desc()).all()
    
    # Analize pe lună
    analyses_by_month = db.session.query(
        func.strftime('%Y-%m', Analysis.data_rezultat).label('month'),
        func.count(Analysis.id).label('count')
    ).group_by(func.strftime('%Y-%m', Analysis.data_rezultat)).order_by('month').all()
    
    return render_template('reports/statistics.html',
                         stats=stats,
                         analyses_by_type=analyses_by_type,
                         analyses_by_month=analyses_by_month)

# API pentru dezvoltări viitoare
@app.route('/api/patients')
def api_patients():
    """API pentru obținerea pacienților"""
    patients = Patient.query.all()
    return jsonify([patient.to_dict() for patient in patients])

@app.route('/api/analyses')
def api_analyses():
    """API pentru obținerea analizelor"""
    analyses = Analysis.query.all()
    return jsonify([analysis.to_dict() for analysis in analyses])

@app.route('/api/patient/<int:patient_id>')
def api_patient(patient_id: int):
    """API pentru obținerea unui pacient specific"""
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict())

@app.route('/api/statistics')
def api_statistics():
    """API pentru obținerea statisticilor"""
    return jsonify(get_statistics())

# Rute pentru căutare și filtrare avansată
@app.route('/search')
def search():
    """Pagina de căutare avansată"""
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    """API pentru căutare"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    results = {}
    
    if search_type in ['all', 'patients']:
        patients = Patient.query.filter(
            (Patient.nume.ilike(f'%{query}%')) |
            (Patient.prenume.ilike(f'%{query}%')) |
            (Patient.cnp.ilike(f'%{query}%'))
        ).limit(10).all()
        results['patients'] = [patient.to_dict() for patient in patients]
    
    if search_type in ['all', 'analyses']:
        analyses = Analysis.query.filter(
            (Analysis.tip_analiza.ilike(f'%{query}%')) |
            (Analysis.rezultat.ilike(f'%{query}%')) |
            (Analysis.medic.ilike(f'%{query}%'))
        ).limit(10).all()
        results['analyses'] = [analysis.to_dict() for analysis in analyses]
    
    return jsonify(results)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handler pentru erroarea 404"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler pentru erroarea 500"""
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template('errors/500.html'), 500

# Inițializare baza de date
def init_db():
    """Inițializează baza de date cu date de test"""
    with app.app_context():
        db.create_all()
        
        # Verifică dacă există deja date
        if Patient.query.first() is None:
            logger.info("Inițializare baza de date cu date de test...")
            
            # Adaugă pacienți de test
            patients_data = [
                {
                    'nume': 'Iordache',
                    'prenume': 'Antonela',
                    'cnp': '2750331270692',
                    'varsta': 47,
                    'sex': 'F',
                    'telefon': '0722123456',
                    'adresa': 'Strada Exemplu, Nr. 1, București'
                },
                {
                    'nume': 'Popescu',
                    'prenume': 'Ion',
                    'cnp': '1800101123456',
                    'varsta': 45,
                    'sex': 'M',
                    'telefon': '0733654321',
                    'adresa': 'Strada Test, Nr. 2, Cluj-Napoca'
                },
                {
                    'nume': 'Marinescu',
                    'prenume': 'Maria',
                    'cnp': '2851205123789',
                    'varsta': 36,
                    'sex': 'F',
                    'telefon': '0744987654',
                    'adresa': 'Bulevardul Libertății, Nr. 15, Timișoara'
                },
                {
                    'nume': 'Georgescu',
                    'prenume': 'Alexandru',
                    'cnp': '1920315234567',
                    'varsta': 32,
                    'sex': 'M',
                    'telefon': '0755111222',
                    'adresa': 'Strada Florilor, Nr. 8, Constanța'
                }
            ]
            
            for patient_data in patients_data:
                patient = Patient(**patient_data)
                db.session.add(patient)
            
            db.session.commit()
            
            # Adaugă analize de test
            analyses_data = [
                {
                    'patient_id': 1,
                    'tip_analiza': 'Hemograma completă',
                    'rezultat': 'Hemoglobina: 12.5 g/dl, Hematocrit: 37%, Leucocite: 6.800/μl',
                    'valori_normale': 'Hb: 12-15 g/dl (F), Ht: 36-46% (F), Leucocite: 4.000-11.000/μl',
                    'observatii': 'Valori în parametri normali',
                    'data_recoltare': date(2024, 1, 15),
                    'data_rezultat': date(2024, 1, 16),
                    'medic': 'Dr. Popescu Ana',
                    'laborator': 'Synevo'
                },
                {
                    'patient_id': 1,
                    'tip_analiza': 'Glicemia',
                    'rezultat': '95 mg/dl',
                    'valori_normale': '70-100 mg/dl',
                    'observatii': 'Valoare normală',
                    'data_recoltare': date(2024, 2, 10),
                    'data_rezultat': date(2024, 2, 10),
                    'medic': 'Dr. Ionescu Mihai',
                    'laborator': 'MedLife'
                },
                {
                    'patient_id': 2,
                    'tip_analiza': 'Profilul lipidic',
                    'rezultat': 'Colesterol total: 185 mg/dl, HDL: 45 mg/dl, LDL: 120 mg/dl',
                    'valori_normale': 'CT: <200 mg/dl, HDL: >40 mg/dl (M), LDL: <130 mg/dl',
                    'observatii': 'Profil lipidic în limite normale',
                    'data_recoltare': date(2024, 1, 20),
                    'data_rezultat': date(2024, 1, 21),
                    'medic': 'Dr. Vasilescu Elena',
                    'laborator': 'Regina Maria'
                },
                {
                    'patient_id': 3,
                    'tip_analiza': 'TSH',
                    'rezultat': '2.1 mIU/L',
                    'valori_normale': '0.4-4.0 mIU/L',
                    'observatii': 'Funcție tiroidiană normală',
                    'data_recoltare': date(2024, 2, 5),
                    'data_rezultat': date(2024, 2, 6),
                    'medic': 'Dr. Radu Cristina',
                    'laborator': 'Synevo'
                }
            ]
            
            for analysis_data in analyses_data:
                analysis = Analysis(**analysis_data)
                db.session.add(analysis)
            
            db.session.commit()
            logger.info("Baza de date inițializată cu succes cu date de test")

# Context processors pentru template-uri
@app.context_processor
def utility_processor():
    """Funcții utilitare disponibile în toate template-urile"""
    def format_date(date_obj):
        if date_obj:
            return date_obj.strftime('%d.%m.%Y')
        return ''
    
    def format_datetime(datetime_obj):
        if datetime_obj:
            return datetime_obj.strftime('%d.%m.%Y %H:%M')
        return ''
    
    def get_age_group(age):
        if age < 18:
            return 'Copil'
        elif age < 65:
            return 'Adult'
        else:
            return 'Senior'
    
    return dict(
        format_date=format_date,
        format_datetime=format_datetime,
        get_age_group=get_age_group,
        current_year=datetime.now().year
    )

if __name__ == '__main__':
    init_db()
    logger.info("Pornire aplicație Flask pe portul 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)