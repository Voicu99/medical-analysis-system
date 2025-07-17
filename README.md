# 🏥 Sistem Management Analize Medicale

Aplicație web dezvoltată în Python Flask pentru gestionarea pacienților și analizelor medicale. Proiect final pentru cursul IT School Python.

## 📋 Descriere Proiect

Sistemul Management Analize Medicale este o aplicație web completă care permite:
- Gestionarea bazei de date cu pacienți
- Înregistrarea și urmărirea analizelor medicale
- Generarea de rapoarte detaliate
- Filtrarea și sortarea avansată a datelor
- Interfață grafică modernă și responsivă

## 🚀 Tehnologii Utilizate

### Backend
- **Python 3.8+** - Limbajul de programare principal
- **Flask 2.3.3** - Framework web micro
- **SQLAlchemy 2.0.21** - ORM pentru baza de date
- **SQLite** - Baza de date (pentru dezvoltare)
- **ReportLab 4.0.4** - Generare PDF pentru rapoarte

### Frontend
- **HTML5 & CSS3** - Structura și stilizarea paginilor
- **Bootstrap 5.3.0** - Framework CSS pentru design responsiv
- **JavaScript ES6+** - Interactivitate client-side
- **Font Awesome 6.4.0** - Iconuri
- **Jinja2** - Template engine

### Dezvoltare
- **Visual Studio Code** - Editor de cod
- **Git** - Control versiune
- **pytest** - Framework de testare

## 📁 Structura Proiect

```
medical-analysis-system/
│
├── app.py                      # Aplicația principală Flask
├── requirements.txt            # Dependințe Python
├── README.md                  # Documentația proiectului
├── medical_analysis.db        # Baza de date SQLite (se generează automat)
├── medical_system.log         # Fișier log (se generează automat)
│
├── templates/                 # Template-uri HTML
│   ├── base.html             # Template de bază
│   ├── index.html            # Pagina principală (dashboard)
│   │
│   ├── patients/             # Template-uri pentru pacienți
│   │   ├── list.html         # Lista pacienți
│   │   ├── add.html          # Adăugare pacient
│   │   ├── edit.html         # Editare pacient
│   │   └── view.html         # Vizualizare detalii pacient
│   │
│   ├── analyses/             # Template-uri pentru analize
│   │   ├── list.html         # Lista analize
│   │   ├── add.html          # Adăugare analiză
│   │   ├── edit.html         # Editare analiză
│   │   └── view.html         # Vizualizare detalii analiză
│   │
│   ├── reports/              # Template-uri pentru rapoarte
│   │   ├── analysis_report.html    # Raport analiză individuală
│   │   ├── patient_report.html     # Raport complet pacient
│   │ 
│   │
│   └── errors/               # Pagini de eroare
│       ├── 404.html          # Pagină nu a fost găsită
│       └── 500.html          # Eroare server


## 🛠️ Instalare și Configurare

### 1. Clonarea Proiectului
```bash
git clone https://github.com/username/medical-analysis-system.git
cd medical-analysis-system
```

### 2. Crearea Mediului Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalarea Dependințelor
```bash
pip install -r requirements.txt
```

### 4. Inițializarea Bazei de Date
```bash
python app.py
```
La prima rulare, aplicația va crea automat baza de date și va popula cu date de test.

### 5. Rularea Aplicației
```bash
python app.py
```

Aplicația va fi disponibilă la: `http://localhost:5000`

## 📊 Funcionalități Implementate

### ✅ CRUD Complet (Create, Read, Update, Delete)
- **Pacienți**: Adăugare, vizualizare, editare, ștergere
- **Analize**: Gestionare completă cu validări

### ✅ Filtrare și Sortare (minim 3 opțiuni)
- **Filtrare pacienți**: după nume, sex, vârstă
- **Filtrare analize**: după pacient, tip, medic, laborator, dată
- **Sortare**: după nume, dată, tip analiză, etc.

### ✅ Generare Rapoarte
- Raport individual pentru fiecare analiză
- Raport complet pentru pacient
- Raport statistici generale
- Export PDF și printare

### ✅ Interfață Grafică Web
- Design modern și responsiv cu Bootstrap 5
- Interfață intuitivă și ușor de folosit
- Compatibilitate mobilă

### ✅ Baza de Date
- SQLite cu SQLAlchemy ORM
- Relații între tabele (One-to-Many)
- Indexare pentru performanță

### ✅ Modularizare și Organizare
- Separarea logicii în funcții
- Template-uri organizate pe categorii
- Cod documentat cu docstrings
- Type hinting pentru funcții
- Logging complet


## 💻 Utilizare

### Dashboard Principal
- Vizualizare statistici generale
- Acces rapid la funcționalități
- Analize recente

### Gestionare Pacienți
1. **Adăugare**: Completați formularul cu datele pacientului
2. **Căutare**: Utilizați filtrele pentru găsirea rapidă
3. **Editare**: Modificați informațiile existente
4. **Vizualizare**: Vedeți profilul complet cu istoric

### Gestionare Analize
1. **Înregistrare**: Adăugați rezultate noi cu validări
2. **Filtrare**: Sortați după multiple criterii
3. **Rapoarte**: Generați documente printabile
4. **Istoric**: Urmăriți evoluția în timp

## 🔧 Dezvoltare și Testare

### Rulare în Modul Development
```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python app.py
```

### Testare
```bash
pytest tests/
```

### Logging
Aplicația generează log-uri în `medical_system.log` pentru debugging și monitoring.

## 🚀 Deployment

### Producție cu Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Variabile de Mediu (pentru producție)
```bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="your-database-url"
```

## 🤝 Contribuție

1. Fork proiectul
2. Creați o ramură pentru funcționalitatea nouă (`git checkout -b feature/AmazingFeature`)
3. Commit schimbările (`git commit -m 'Add some AmazingFeature'`)
4. Push în ramură (`git push origin feature/AmazingFeature`)
5. Deschideți un Pull Request

## 📝 TODO List (Dezvoltări Viitoare)

- [ ] Sistem de autentificare și autorizare
- [ ] Export Excel pentru rapoarte
- [ ] API REST pentru integrări externe
- [ ] Notificări email pentru rezultate
- [ ] Backup automat al bazei de date
- [ ] Grafice și statistici avansate
- [ ] Aplicație mobilă
- [ ] Integrare cu sisteme medicale existente

## 📄 Licență

Acest proiect este dezvoltat pentru scop educațional în cadrul cursului IT School Python.


---

*Dezvoltat cu ❤️ în Python Flask pentru IT School*






# Sistem Management Analize Medicale

Aplicație web pentru gestionarea pacienților și analizelor medicale, dezvoltată în Flask.

## Funcționalități

- 👥 Gestionare pacienți (CRUD)
- 🧪 Gestionare analize medicale (CRUD)
- 📊 Generare rapoarte
- 🔍 Căutare și filtrare
- 📱 Design responsive

## Tehnologii

- **Backend:** Python Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap
- **Template Engine:** Jinja2

## Instalare

```bash
# Clonează repository-ul
git clone https://github.com/USERNAME/medical-analysis-system.git
cd medical-analysis-system

# Instalează dependențele
pip install -r requirements.txt

# Rulează aplicația
python app.py
Utilizare

Accesează http://127.0.0.1:5000
Adaugă pacienți noi
Creează analize pentru pacienți
Generează rapoarte

Autor
Dezvoltat de Librimir Voicu - Proiect final IT School
