#!/usr/bin/env python3
"""
Script pentru rularea aplicației Sistem Management Analize Medicale
Oferă opțiuni pentru diferite moduri de rulare

Usage:
    python run.py                    # Rulare normală
    python run.py --debug            # Rulare cu debug
    python run.py --production       # Rulare pentru producție
    python run.py --init-db          # Doar inițializare baza de date
    python run.py --reset-db         # Resetare completă baza de date
"""

import argparse
import sys
import os
from pathlib import Path

# Adaugă directorul curent în calea Python
sys.path.insert(0, str(Path(__file__).parent))

from app import app, init_db, db

def run_development():
    """Rulează aplicația în modul dezvoltare"""
    print("🚀 Pornire aplicație în modul dezvoltare...")
    print("📝 URL: http://localhost:5000")
    print("🔧 Debug: Activat")
    print("📊 Baza de date: SQLite (dezvoltare)")
    print("-" * 50)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )

def run_production():
    """Rulează aplicația în modul producție"""
    print("🏭 Pornire aplicație în modul producție...")
    print("📝 URL: http://localhost:8000")
    print("🔒 Debug: Dezactivat")
    print("⚡ Server: Gunicorn")
    print("-" * 50)
    
    try:
        import gunicorn
        os.system("gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile - --error-logfile - app:app")
    except ImportError:
        print("❌ Gunicorn nu este instalat!")
        print("💡 Instalați cu: pip install gunicorn")
        print("🔄 Rulez cu serverul Flask integrat...")
        app.run(debug=False, host='0.0.0.0', port=8000)

def init_database():
    """Inițializează baza de date"""
    print("🗄️ Inițializare baza de date...")
    
    try:
        init_db()
        print("✅ Baza de date inițializată cu succes!")
        print("📊 Pacienți de test adăugați")
        print("🧪 Analize de test adăugate")
    except Exception as e:
        print(f"❌ Eroare la inițializarea bazei de date: {e}")
        return False
    
    return True

def reset_database():
    """Resetează complet baza de date"""
    print("⚠️ Resetare completă baza de date...")
    
    response = input("Sigur doriți să ștergeți toate datele? (da/nu): ")
    if response.lower() not in ['da', 'yes', 'y']:
        print("❌ Operațiunea a fost anulată")
        return False
    
    try:
        # Șterge fișierul bazei de date
        db_file = 'medical_analysis.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ Fișierul {db_file} a fost șters")
        
        # Recreează baza de date
        with app.app_context():
            db.drop_all()
            db.create_all()
            print("🔄 Baza de date recreată")
        
        # Inițializează cu date noi
        init_db()
        print("✅ Baza de date resetată și reinițializată cu succes!")
        
    except Exception as e:
        print(f"❌ Eroare la resetarea bazei de date: {e}")
        return False
    
    return True

def check_requirements():
    """Verifică dacă toate dependințele sunt instalate"""
    print("🔍 Verificare dependințe...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'reportlab'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Pachete lipsă: {', '.join(missing_packages)}")
        print("💡 Instalați cu: pip install -r requirements.txt")
        return False
    
    print("✅ Toate dependințele sunt instalate!")
    return True

def show_system_info():
    """Afișează informații despre sistem"""
    print("=" * 60)
    print("🏥 SISTEM MANAGEMENT ANALIZE MEDICALE")
    print("=" * 60)
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Director: {os.getcwd()}")
    print(f"💾 Baza de date: {'✅ Există' if os.path.exists('medical_analysis.db') else '❌ Nu există'}")
    print(f"📋 Requirements: {'✅ OK' if os.path.exists('requirements.txt') else '❌ Lipsă'}")
    print("=" * 60)

def main():
    """Funcția principală"""
    parser = argparse.ArgumentParser(
        description='Sistem Management Analize Medicale',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemple de utilizare:
  python run.py                 Rulare normală (dezvoltare)
  python run.py --debug         Rulare cu debug explicit
  python run.py --production    Rulare pentru producție
  python run.py --init-db       Doar inițializare baza de date
  python run.py --reset-db      Resetare completă baza de date
  python run.py --check         Verificare dependințe
        """
    )
    
    parser.add_argument('--debug', action='store_true', 
                       help='Rulează în modul debug')
    parser.add_argument('--production', action='store_true',
                       help='Rulează în modul producție')
    parser.add_argument('--init-db', action='store_true',
                       help='Inițializează baza de date')
    parser.add_argument('--reset-db', action='store_true',
                       help='Resetează complet baza de date')
    parser.add_argument()