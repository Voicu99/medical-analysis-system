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
import random
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

# Funcții utilitare pentru validare CNP
def validate_cnp(cnp: str) -> bool:
    """
    Validează CNP-ul românesc conform algoritmului oficial
    
    Args:
        cnp (str): CNP-ul de validat (13 cifre)
        
    Returns:
        bool: True dacă CNP-ul este valid, False altfel
    """
    # Verificare lungime și format
    if not cnp or len(cnp) != 13:
        return False
    
    # Verificare dacă toate caracterele sunt cifre
    if not cnp.isdigit():
        return False
    
    # Verificare prima cifră (sex și secol)
    if cnp[0] not in '12345678':
        return False
    
    try:
        # Verificare luna
        luna = int(cnp[3:5])
        if luna < 1 or luna > 12:
            return False
        
        # Verificare ziua
        zi = int(cnp[5:7])
        if zi < 1 or zi > 31:
            return False
        
        # Calculul cifrei de control
        coeficienti = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
        suma = sum(int(cnp[i]) * coeficienti[i] for i in range(12))
        
        rest = suma % 11
        cifra_control = 1 if rest == 10 else rest
        
        return cifra_control == int(cnp[12])
        
    except (ValueError, IndexError):
        return False


def validate_cnp_detailed(cnp: str) -> tuple[bool, str]:
    """
    Validează CNP-ul și returnează mesajul de eroare detaliat
    
    Args:
        cnp (str): CNP-ul de validat
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not cnp:
        return False, "CNP-ul nu poate fi gol"
    
    if len(cnp) != 13:
        return False, "CNP-ul trebuie să aibă exact 13 cifre"
    
    if not cnp.isdigit():
        return False, "CNP-ul trebuie să conțină doar cifre"
    
    if cnp[0] not in '12345678':
        return False, "Prima cifră a CNP-ului este invalidă (trebuie să fie 1-8)"
    
    try:
        # Verificare anul nașterii
        an = int(cnp[1:3])
        if cnp[0] in '12':  # secolul XX (1900-1999)
            an_complet = 1900 + an
        elif cnp[0] in '34':  # secolul XIX (1800-1899)
            an_complet = 1800 + an
        elif cnp[0] in '56':  # secolul XXI (2000-2099)
            an_complet = 2000 + an
        elif cnp[0] in '78':  # secolul XVIII (1700-1799)
            an_complet = 1700 + an
        
        # Verificare anul să fie rezonabil
        anul_curent = datetime.now().year
        if an_complet < 1900 or an_complet > anul_curent:
            return False, f"Anul nașterii ({an_complet}) nu este valid"
        
        # Verificare luna
        luna = int(cnp[3:5])
        if luna < 1 or luna > 12:
            return False, "Luna din CNP este invalidă (trebuie să fie 01-12)"
        
        # Verificare ziua
        zi = int(cnp[5:7])
        if zi < 1 or zi > 31:
            return False, "Ziua din CNP este invalidă (trebuie să fie 01-31)"
        
        # Calculul cifrei de control
        coeficienti = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
        suma = sum(int(cnp[i]) * coeficienti[i] for i in range(12))
        
        rest = suma % 11
        cifra_control = 1 if rest == 10 else rest
        
        if cifra_control != int(cnp[12]):
            return False, "Cifra de control a CNP-ului este incorectă"
        
        return True, "CNP valid"
        
    except (ValueError, IndexError):
        return False, "CNP-ul conține caractere invalide"


def extract_info_from_cnp(cnp: str) -> Optional[Dict]:
    """
    Extrage informații din CNP (sex, vârstă, data nașterii)
    
    Args:
        cnp (str): CNP-ul valid
        
    Returns:
        dict: Informații extrase din CNP sau None dacă CNP invalid
    """
    if not validate_cnp(cnp):
        return None
    
    try:
        prima_cifra = int(cnp[0])
        
        # Determinare sex
        sex = 'M' if prima_cifra % 2 == 1 else 'F'
        
        # Determinare secolul
        if prima_cifra in [1, 2]:
            secol = 1900
        elif prima_cifra in [3, 4]:
            secol = 1800
        elif prima_cifra in [5, 6]:
            secol = 2000
        elif prima_cifra in [7, 8]:
            secol = 1700
        else:
            return None
        
        # Extragere date
        an = secol + int(cnp[1:3])
        luna = int(cnp[3:5])
        zi = int(cnp[5:7])
        
        # Calculare vârstă
        today = datetime.now()
        birth_date = datetime(an, luna, zi)
        varsta = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            varsta -= 1
        
        return {
            'sex': sex,
            'an': an,
            'luna': luna,
            'zi': zi,
            'varsta': varsta,
            'data_nasterii': f"{zi:02d}.{luna:02d}.{an}"
        }
        
    except (ValueError, IndexError):
        return None


# Funcții pentru generarea automată de medici și laboratoare
def generate_random_doctor():
    """Generează un nume de medic aleatoriu"""
    prenume_medici = [
        'Ana', 'Maria', 'Elena', 'Cristina', 'Ioana', 'Mihaela', 'Gabriela', 'Alina',
        'Ion', 'Mihai', 'Alexandru', 'Andrei', 'Stefan', 'Radu', 'Bogdan', 'Cristian',
        'Luminita', 'Carmen', 'Diana', 'Raluca', 'Andreea', 'Simona', 'Daniela',
        'Daniel', 'Florin', 'Marius', 'Adrian', 'Gheorghe', 'Vasile', 'Nicolae'
    ]
    
    nume_medici = [
        'Popescu', 'Ionescu', 'Popa', 'Stoica', 'Dumitrescu', 'Georgescu', 
        'Constantinescu', 'Marin', 'Tudor', 'Radu', 'Vasilescu', 'Nicolae',
        'Stanescu', 'Moldovan', 'Oprea', 'Diaconu', 'Niculescu', 'Barbu',
        'Petrescu', 'Ciobanu', 'Stefan', 'Florea', 'Preda', 'Lazar'
    ]
    
    prenume = random.choice(prenume_medici)
    nume = random.choice(nume_medici)
    
    return f"Dr. {nume} {prenume}"


def generate_random_laboratory():
    """Generează un nume de laborator aleatoriu"""
    laboratoare = [
        'Synevo',
        'MedLife',
        'Regina Maria',
        'Bioclinica',
        'Lifecare',
        'Sanador',
        'Medicover',
        'Gral Medical',
        'Medis',
        'Biotest',
        'Euroclinic',
        'Centrul Medical Excellence',
        'Policlinica de Diagnostic Rapid',
        'Laboratorul Central',
        'Bio Labs',
        'MedCenter',
        'Clinic Lab',
        'Alpha Lab',
        'Prima Lab',
        'Expert Medical'
    ]
    
    return random.choice(laboratoare)


def get_analysis_suggestions():
    """Returnează sugestii de analize pe categorii"""
    return {
        'Analize de bază': [
            'Hemograma completă',
            'Glicemia',
            'Colesterol total',
            'Trigliceride',
            'Creatinina',
            'Uree'
        ],
        'Analize hormonale': [
            'TSH',
            'T3',
            'T4',
            'Cortizol',
            'Testosteron',
            'Estradiol'
        ],
        'Analize cardiace': [
            'Profilul lipidic',
            'HDL Colesterol',
            'LDL Colesterol',
            'CK-MB',
            'Troponina'
        ],
        'Analize hepatice': [
            'ALAT (ALT)',
            'ASAT (AST)',
            'Bilirubina totală',
            'Bilirubina directă',
            'Fosfataza alcalină'
        ],
        'Analize inflamatorii': [
            'Proteina C reactivă',
            'VSH',
            'Fibrinogen',
            'Procalcitonina'
        ],
        'Analize urinare': [
            'Examen complet de urină',
            'Urocultura',
            'Microalbuminuria',
            'Proteinuria de 24h'
        ],
        'Vitamine și minerale': [
            'Vitamina D',
            'Vitamina B12',
            'Acid folic',
            'Fier seric',
            'Ferritina',
            'Magneziu'
        ]
    }


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
            # Validare CNP cu mesaj detaliat
            cnp = request.form['cnp'].strip()
            
            # Folosește funcția detaliată pentru debugging
            is_valid, error_message = validate_cnp_detailed(cnp)
            
            if not is_valid:
                flash(f'CNP invalid: {error_message}', 'error')
                return render_template('patients/add.html')
            
            # Verificare unicitate CNP
            existing_patient = Patient.query.filter_by(cnp=cnp).first()
            if existing_patient:
                flash('Există deja un pacient cu acest CNP!', 'error')
                return render_template('patients/add.html')
            
            # Extrage informații din CNP pentru auto-completare
            cnp_info = extract_info_from_cnp(cnp)
            
            # Folosește informațiile din CNP dacă sunt disponibile
            sex_form = request.form.get('sex', '')
            varsta_form = request.form.get('varsta', '')
            
            if cnp_info:
                # Auto-completează sex și vârstă dacă nu sunt specificate
                if not sex_form:
                    sex_form = cnp_info['sex']
                if not varsta_form:
                    varsta_form = str(cnp_info['varsta'])
            
            patient = Patient(
                nume=request.form['nume'].strip().title(),
                prenume=request.form['prenume'].strip().title(),
                cnp=cnp,
                varsta=int(varsta_form) if varsta_form else 0,
                sex=sex_form,
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
            is_valid, error_message = validate_cnp_detailed(cnp)
            
            if not is_valid:
                flash(f'CNP invalid: {error_message}', 'error')
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

# API pentru validarea CNP în timp real
@app.route('/api/validate-cnp/<cnp>')
def api_validate_cnp(cnp):
    """API pentru validarea CNP în timp real"""
    is_valid, message = validate_cnp_detailed(cnp)
    cnp_info = extract_info_from_cnp(cnp) if is_valid else None
    
    return jsonify({
        'valid': is_valid,
        'message': message,
        'info': cnp_info
    })

# Ruta de test pentru CNP
@app.route('/test-cnp/<cnp>')
def test_cnp(cnp):
    """Rută de test pentru validarea CNP"""
    is_valid, message = validate_cnp_detailed(cnp)
    cnp_info = extract_info_from_cnp(cnp)
    
    return jsonify({
        'cnp': cnp,
        'is_valid': is_valid,
        'message': message,
        'simple_validation': validate_cnp(cnp),
        'extracted_info': cnp_info
    })

# API pentru generare dinamică de medici și laboratoare
@app.route('/api/generate-doctor')
def api_generate_doctor():
    """API pentru generarea unui medic aleatoriu"""
    return jsonify({
        'doctor': generate_random_doctor()
    })

@app.route('/api/generate-laboratory')
def api_generate_laboratory():
    """API pentru generarea unui laborator aleatoriu"""
    return jsonify({
        'laboratory': generate_random_laboratory()
    })

@app.route('/api/analysis-suggestions')
def api_analysis_suggestions():
    """API pentru sugestii de analize"""
    return jsonify(get_analysis_suggestions())

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
    """Adăugare analiză nouă cu generare automată medic/laborator"""
    if request.method == 'POST':
        try:
            # Validare date
            data_recoltare = datetime.strptime(request.form['data_recoltare'], '%Y-%m-%d').date()
            data_rezultat = datetime.strptime(request.form['data_rezultat'], '%Y-%m-%d').date()
            
            if data_rezultat < data_recoltare:
                flash('Data rezultatului nu poate fi anterioară datei recoltării!', 'error')
                patients = Patient.query.order_by(Patient.nume).all()
                return render_template('analyses/add.html', 
                                     patients=patients,
                                     random_doctor=generate_random_doctor(),
                                     random_laboratory=generate_random_laboratory(),
                                     analysis_suggestions=get_analysis_suggestions())
            
            # Generează medic și laborator dacă nu sunt specificate
            medic = request.form.get('medic', '').strip()
            laborator = request.form.get('laborator', '').strip()
            
            if not medic:
                medic = generate_random_doctor()
                flash(f'Medic generat automat: {medic}', 'info')
            
            if not laborator:
                laborator = generate_random_laboratory()
                flash(f'Laborator generat automat: {laborator}', 'info')
            
            analysis = Analysis(
                patient_id=int(request.form['patient_id']),
                tip_analiza=request.form['tip_analiza'].strip(),
                rezultat=request.form['rezultat'].strip(),
                valori_normale=request.form.get('valori_normale', '').strip(),
                observatii=request.form.get('observatii', '').strip(),
                data_recoltare=data_recoltare,
                data_rezultat=data_rezultat,
                medic=medic,
                laborator=laborator
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
    return render_template('analyses/add.html', 
                         patients=patients,
                         random_doctor=generate_random_doctor(),
                         random_laboratory=generate_random_laboratory(),
                         analysis_suggestions=get_analysis_suggestions())

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

# GENERARE RAPOARTE - Secțiunea corectată pentru toate fișierele
@app.route('/reports/analysis/<int:analysis_id>')
def generate_analysis_report(analysis_id: int):
    """Generare raport pentru o analiză"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    return render_template('reports/analysis_reports.html', 
                         analysis=analysis,
                         patient=analysis.patient)

@app.route('/reports/patient/<int:patient_id>')
def generate_patient_report(patient_id: int):
    """Generare raport complet pentru un pacient"""
    patient = Patient.query.get_or_404(patient_id)
    analyses = Analysis.query.filter_by(patient_id=patient_id).order_by(Analysis.data_rezultat.desc()).all()
    
    return render_template('reports/patient_reports.html', 
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

# FUNCȚII PDF pentru rapoarte
@app.route('/reports/analysis/<int:analysis_id>/pdf')
def generate_analysis_pdf(analysis_id: int):
    """Generare PDF pentru o analiză"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Crearea PDF-ului
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "RAPORT ANALIZA MEDICALA")
    
    # Informații pacient
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 100, "INFORMATII PACIENT:")
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 120, f"Nume: {analysis.patient.nume} {analysis.patient.prenume}")
    p.drawString(50, height - 135, f"CNP: {analysis.patient.cnp}")
    p.drawString(50, height - 150, f"Varsta: {analysis.patient.varsta} ani")
    p.drawString(50, height - 165, f"Sex: {'Masculin' if analysis.patient.sex == 'M' else 'Feminin'}")
    
    # Informații analiză
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 200, "INFORMATII ANALIZA:")
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 220, f"Tip: {analysis.tip_analiza}")
    p.drawString(50, height - 235, f"Data recoltare: {analysis.data_recoltare.strftime('%d.%m.%Y')}")
    p.drawString(50, height - 250, f"Data rezultat: {analysis.data_rezultat.strftime('%d.%m.%Y')}")
    p.drawString(50, height - 265, f"Medic: {analysis.medic or 'Nu este specificat'}")
    p.drawString(50, height - 280, f"Laborator: {analysis.laborator or 'Nu este specificat'}")
    
    # Rezultate
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 315, "REZULTATE:")
    p.setFont("Helvetica", 11)
    
    # Împărțim rezultatul în linii
    rezultat_lines = analysis.rezultat.split('\n')
    y_pos = height - 335
    for line in rezultat_lines:
        if y_pos < 100:  # Pagină nouă dacă nu mai avem spațiu
            p.showPage()
            y_pos = height - 50
        p.drawString(50, y_pos, line[:80])  # Limitare la 80 caractere per linie
        y_pos -= 15
    
    # Valori normale
    if analysis.valori_normale:
        y_pos -= 20
        if y_pos < 100:
            p.showPage()
            y_pos = height - 50
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "VALORI NORMALE:")
        p.setFont("Helvetica", 11)
        p.drawString(50, y_pos - 20, analysis.valori_normale)
        y_pos -= 40
    
    # Observații
    if analysis.observatii:
        if y_pos < 100:
            p.showPage()
            y_pos = height - 50
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "OBSERVATII:")
        p.setFont("Helvetica", 11)
        observatii_lines = analysis.observatii.split('\n')
        for line in observatii_lines:
            if y_pos < 100:
                p.showPage()
                y_pos = height - 50
            p.drawString(50, y_pos - 20, line[:80])
            y_pos -= 15
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(50, 50, f"Generat la: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    p.drawString(50, 35, "Sistem Management Analize Medicale")
    
    p.save()
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=analiza_{analysis.id}_{analysis.patient.nume}_{analysis.patient.prenume}.pdf'
    
    return response

@app.route('/reports/patient/<int:patient_id>/pdf')
def generate_patient_pdf(patient_id: int):
    """Generare PDF pentru toate analizele unui pacient"""
    patient = Patient.query.get_or_404(patient_id)
    analyses = Analysis.query.filter_by(patient_id=patient_id).order_by(Analysis.data_rezultat.desc()).all()
    
    # Crearea PDF-ului
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "RAPORT COMPLET PACIENT")
    
    # Informații pacient
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 100, "INFORMATII PACIENT:")
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 120, f"Nume: {patient.nume} {patient.prenume}")
    p.drawString(50, height - 135, f"CNP: {patient.cnp}")
    p.drawString(50, height - 150, f"Varsta: {patient.varsta} ani")
    p.drawString(50, height - 165, f"Sex: {'Masculin' if patient.sex == 'M' else 'Feminin'}")
    p.drawString(50, height - 180, f"Telefon: {patient.telefon or 'Nu este specificat'}")
    p.drawString(50, height - 195, f"Adresa: {patient.adresa or 'Nu este specificata'}")
    
    y_pos = height - 230
    
    if analyses:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, f"ISTORIC ANALIZE ({len(analyses)} analize):")
        y_pos -= 30
        
        for i, analysis in enumerate(analyses, 1):
            if y_pos < 150:  # Pagină nouă
                p.showPage()
                y_pos = height - 50
            
            p.setFont("Helvetica-Bold", 11)
            p.drawString(50, y_pos, f"{i}. {analysis.tip_analiza}")
            y_pos -= 15
            
            p.setFont("Helvetica", 10)
            p.drawString(70, y_pos, f"Data: {analysis.data_rezultat.strftime('%d.%m.%Y')}")
            y_pos -= 12
            p.drawString(70, y_pos, f"Medic: {analysis.medic or 'Nu specificat'}")
            y_pos -= 12
            p.drawString(70, y_pos, f"Laborator: {analysis.laborator or 'Nu specificat'}")
            y_pos -= 12
            
            # Rezultat (primele 100 caractere)
            rezultat_scurt = analysis.rezultat[:100] + "..." if len(analysis.rezultat) > 100 else analysis.rezultat
            p.drawString(70, y_pos, f"Rezultat: {rezultat_scurt}")
            y_pos -= 20
    else:
        p.setFont("Helvetica", 11)
        p.drawString(50, y_pos, "Nu exista analize pentru acest pacient.")
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(50, 50, f"Generat la: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    p.drawString(50, 35, "Sistem Management Analize Medicale")
    
    p.save()
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=pacient_{patient.nume}_{patient.prenume}_complet.pdf'
    
    return response

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
            
            # Adaugă pacienți de test cu CNP-uri valide
            patients_data = [
                {
                    'nume': 'Popescu',
                    'prenume': 'Ion',
                    'cnp': '1900315234567',  # Masculin, 15.03.1990
                    'varsta': 34,
                    'sex': 'M',
                    'telefon': '0722123456',
                    'adresa': 'Strada Exemplu, Nr. 1, București'
                },
                {
                    'nume': 'Ionescu',
                    'prenume': 'Maria',
                    'cnp': '2851205123456',  # Feminin, 05.12.1985
                    'varsta': 38,
                    'sex': 'F',
                    'telefon': '0733654321',
                    'adresa': 'Strada Test, Nr. 2, Cluj-Napoca'
                },
                {
                    'nume': 'Marinescu',
                    'prenume': 'Alexandru',
                    'cnp': '5000101234567',  # Masculin, 01.01.2000
                    'varsta': 24,
                    'sex': 'M',
                    'telefon': '0744987654',
                    'adresa': 'Bulevardul Libertății, Nr. 15, Timișoara'
                },
                {
                    'nume': 'Georgescu',
                    'prenume': 'Ana',
                    'cnp': '6950630123456',  # Feminin, 30.06.1995
                    'varsta': 29,
                    'sex': 'F',
                    'telefon': '0755111222',
                    'adresa': 'Strada Florilor, Nr. 8, Constanța'
                }
            ]
            
            for patient_data in patients_data:
                # Verifică CNP-ul înainte de adăugare
                if validate_cnp(patient_data['cnp']):
                    patient = Patient(**patient_data)
                    db.session.add(patient)
                else:
                    logger.warning(f"CNP invalid pentru pacientul {patient_data['nume']}: {patient_data['cnp']}")
            
            db.session.commit()
            
            # Adaugă analize de test cu medici și laboratoare generate
            analyses_data = [
                {
                    'patient_id': 1,
                    'tip_analiza': 'Hemograma completă',
                    'rezultat': 'Hemoglobina: 12.5 g/dl, Hematocrit: 37%, Leucocite: 6.800/μl',
                    'valori_normale': 'Hb: 12-15 g/dl (F), Ht: 36-46% (F), Leucocite: 4.000-11.000/μl',
                    'observatii': 'Valori în parametri normali',
                    'data_recoltare': date(2024, 1, 15),
                    'data_rezultat': date(2024, 1, 16),
                    'medic': generate_random_doctor(),
                    'laborator': generate_random_laboratory()
                },
                {
                    'patient_id': 1,
                    'tip_analiza': 'Glicemia',
                    'rezultat': '95 mg/dl',
                    'valori_normale': '70-100 mg/dl',
                    'observatii': 'Valoare normală',
                    'data_recoltare': date(2024, 2, 10),
                    'data_rezultat': date(2024, 2, 10),
                    'medic': generate_random_doctor(),
                    'laborator': generate_random_laboratory()
                },
                {
                    'patient_id': 2,
                    'tip_analiza': 'Profilul lipidic',
                    'rezultat': 'Colesterol total: 185 mg/dl, HDL: 45 mg/dl, LDL: 120 mg/dl',
                    'valori_normale': 'CT: <200 mg/dl, HDL: >40 mg/dl (M), LDL: <130 mg/dl',
                    'observatii': 'Profil lipidic în limite normale',
                    'data_recoltare': date(2024, 1, 20),
                    'data_rezultat': date(2024, 1, 21),
                    'medic': generate_random_doctor(),
                    'laborator': generate_random_laboratory()
                },
                {
                    'patient_id': 3,
                    'tip_analiza': 'TSH',
                    'rezultat': '2.1 mIU/L',
                    'valori_normale': '0.4-4.0 mIU/L',
                    'observatii': 'Funcție tiroidiană normală',
                    'data_recoltare': date(2024, 2, 5),
                    'data_rezultat': date(2024, 2, 6),
                    'medic': generate_random_doctor(),
                    'laborator': generate_random_laboratory()
                },
                {
                    'patient_id': 4,
                    'tip_analiza': 'Creatinina',
                    'rezultat': '0.9 mg/dl',
                    'valori_normale': '0.5-1.0 mg/dl (F), 0.6-1.2 mg/dl (M)',
                    'observatii': 'Funcție renală normală',
                    'data_recoltare': date(2024, 2, 15),
                    'data_rezultat': date(2024, 2, 16),
                    'medic': generate_random_doctor(),
                    'laborator': generate_random_laboratory()
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
        current_year=datetime.now().year,
        datetime=datetime
    )

if __name__ == '__main__':
    init_db()
    logger.info("Pornire aplicație Flask pe portul 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
