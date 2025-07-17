"""
Script de instalare automată pentru Sistem Management Analize Medicale
Automatizează procesul de setup pentru dezvoltare și producție

Usage:
    python install.py                # Instalare completă
    python install.py --dev          # Doar pentru dezvoltare
    python install.py --prod         # Pentru producție
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class Colors:
    """Clase pentru colorarea output-ului în terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKGREEN):
    """Printează mesaj colorat"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Printează header colorat"""
    print("\n" + "="*60)
    print_colored(f" {message} ", Colors.HEADER + Colors.BOLD)
    print("="*60)

def check_python_version():
    """Verifică versiunea Python"""
    print_header("VERIFICARE VERSIUNE PYTHON")
    
    version = sys.version_info
    print(f"Versiunea curentă: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("❌ EROARE: Necesită Python 3.8 sau mai nou!", Colors.FAIL)
        print_colored("💡 Descărcați de la: https://www.python.org/downloads/", Colors.WARNING)
        return False
    
    print_colored("✅ Versiunea Python este compatibilă!", Colors.OKGREEN)
    return True

def check_pip():
    """Verifică dacă pip este instalat"""
    print_header("VERIFICARE PIP")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_colored(f"✅ {result.stdout.strip()}", Colors.OKGREEN)
            return True
        else:
            print_colored("❌ Pip nu este disponibil!", Colors.FAIL)
            return False
    except Exception as e:
        print_colored(f"❌ Eroare la verificarea pip: {e}", Colors.FAIL)
        return False

def create_virtual_environment():
    """Creează mediul virtual"""
    print_header("CREARE MEDIU VIRTUAL")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_colored("📁 Mediul virtual există deja", Colors.WARNING)
        response = input("Doriți să-l recreați? (da/nu): ")
        if response.lower() in ['da', 'yes', 'y']:
            import shutil
            shutil.rmtree(venv_path)
            print_colored("🗑️ Mediul virtual vechi a fost șters", Colors.OKBLUE)
        else:
            print_colored("⏭️ Se folosește mediul virtual existent", Colors.OKBLUE)
            return True
    
    try:
        print_colored("🔧 Creare mediu virtual...", Colors.OKBLUE)
        result = subprocess.run([sys.executable, "-m", "venv", "venv"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_colored("✅ Mediul virtual a fost creat cu succes!", Colors.OKGREEN)
            return True
        else:
            print_colored(f"❌ Eroare la crearea mediului virtual: {result.stderr}", Colors.FAIL)
            return False
            
    except Exception as e:
        print_colored(f"❌ Eroare neașteptată: {e}", Colors.FAIL)
        return False

def get_activation_command():
    """Returnează comanda de activare pentru mediul virtual"""
    system = platform.system().lower()
    
    if system == "windows":
        return "venv\\Scripts\\activate.bat"
    else:
        return "source venv/bin/activate"

def install_requirements():
    """Instalează dependințele"""
    print_header("INSTALARE DEPENDINȚE")
    
    # Determină calea către pip din mediul virtual
    system = platform.system().lower()
    if system == "windows":
        pip_path = Path("venv/Scripts/pip.exe")
    else:
        pip_path = Path("venv/bin/pip")
    
    if not pip_path.exists():
        print_colored("❌ Pip nu a fost găsit în mediul virtual!", Colors.FAIL)
        return False
    
    try:
        print_colored("📦 Instalare dependințe...", Colors.OKBLUE)
        
        # Upgrade pip
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print_colored("✅ Pip actualizat", Colors.OKGREEN)
        
        # Instalează requirements
        result = subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_colored("✅ Toate dependințele au fost instalate!", Colors.OKGREEN)
            
            # Afișează pachetele instalate
            print_colored("\n📋 Pachete instalate:", Colors.OKBLUE)
            installed = subprocess.run([str(pip_path), "list"], 
                                     capture_output=True, text=True)
            print(installed.stdout)
            
            return True
        else:
            print_colored(f"❌ Eroare la instalarea dependințelor:", Colors.FAIL)
            print(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Eroare la instalare: {e}", Colors.FAIL)
        return False
    except Exception as e:
        print_colored(f"❌ Eroare neașteptată: {e}", Colors.FAIL)
        return False

def create_directories():
    """Creează directoarele necesare"""
    print_header("CREARE STRUCTURĂ DIRECTOARE")
    
    directories = [
        "templates/patients",
        "templates/analyses", 
        "templates/reports",
        "templates/errors",
        "static/css",
        "static/js",
        "static/images",
        "uploads",
        "logs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_colored(f"📁 Creat: {directory}", Colors.OKGREEN)
        else:
            print_colored(f"📁 Există: {directory}", Colors.OKBLUE)
    
    print_colored("✅ Structura de directoare este completă!", Colors.OKGREEN)

def setup_database():
    """Configurează baza de date"""
    print_header("CONFIGURARE BAZA DE DATE")
    
    # Determină calea către python din mediul virtual
    system = platform.system().lower()
    if system == "windows":
        python_path = Path("venv/Scripts/python.exe")
    else:
        python_path = Path("venv/bin/python")
    
    try:
        print_colored("🗄️ Inițializare baza de date...", Colors.OKBLUE)
        
        # Rulează scriptul de inițializare
        result = subprocess.run([str(python_path), "run.py", "--init-db"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_colored("✅ Baza de date inițializată cu succes!", Colors.OKGREEN)
            print_colored("📊 Date de test adăugate", Colors.OKBLUE)
            return True
        else:
            print_colored(f"❌ Eroare la inițializarea bazei de date:", Colors.FAIL)
            print(result.stderr)
            return False
            
    except Exception as e:
        print_colored(f"❌ Eroare neașteptată: {e}", Colors.FAIL)
        return False

def create_run_scripts():
    """Creează script-uri de rulare"""
    print_header("CREARE SCRIPT-URI RULARE")
    
    system = platform.system().lower()
    
    if system == "windows":
        # Script Windows (.bat)
        windows_script = """@echo off
echo Pornire Sistem Management Analize Medicale...
call venv\\Scripts\\activate.bat
python run.py
pause
"""
        with open("start.bat", "w", encoding="utf-8") as f:
            f.write(windows_script)
        print_colored("✅ Creat: start.bat", Colors.OKGREEN)
        
    else:
        # Script Linux/Mac (.sh)
        unix_script = """#!/bin/bash
echo "Pornire Sistem Management Analize Medicale..."
source venv/bin/activate
python run.py
"""
        with open("start.sh", "w", encoding="utf-8") as f:
            f.write(unix_script)
        
        # Face script-ul executabil
        os.chmod("start.sh", 0o755)
        print_colored("✅ Creat: start.sh", Colors.OKGREEN)

def show_completion_message():
    """Afișează mesajul de finalizare"""
    print_header("INSTALARE COMPLETĂ!")
    
    system = platform.system().lower()
    activation_cmd = get_activation_command()
    
    print_colored("🎉 Instalarea s-a finalizat cu succes!", Colors.OKGREEN)
    print_colored("\n📋 Următorii pași:", Colors.OKBLUE)
    
    print(f"1. Activați mediul virtual:")
    print_colored(f"   {activation_cmd}", Colors.OKCYAN)
    
    print(f"\n2. Porniți aplicația:")
    if system == "windows":
        print_colored("   start.bat", Colors.OKCYAN)
        print_colored("   SAU: python run.py", Colors.OKCYAN)
    else:
        print_colored("   ./start.sh", Colors.OKCYAN)
        print_colored("   SAU: python run.py", Colors.OKCYAN)
    
    print(f"\n3. Deschideți browser-ul la:")
    print_colored("   http://localhost:5000", Colors.OKCYAN)
    
    print(f"\n📊 Date de test disponibile:")
    print_colored("   • Pacienți: 4 pacienți de test", Colors.OKBLUE)
    print_colored("   • Analize: Diverse tipuri de analize", Colors.OKBLUE)
    
    print(f"\n🔧 Comenzi utile:")
    print_colored("   python run.py --help     # Ajutor", Colors.OKCYAN)
    print_colored("   python run.py --reset-db # Resetare baza de date", Colors.OKCYAN)
    print_colored("   python run.py --check    # Verificare dependințe", Colors.OKCYAN)

def main():
    """Funcția principală de instalare"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Installer pentru Sistem Management Analize Medicale')
    parser.add_argument('--dev', action='store_true', help='Instalare pentru dezvoltare')
    parser.add_argument('--prod', action='store_true', help='Instalare pentru producție')
    
    args = parser.parse_args()
    
    print_colored("🏥 INSTALLER SISTEM MANAGEMENT ANALIZE MEDICALE", Colors.HEADER + Colors.BOLD)
    print_colored("Versiunea 1.0 - IT School Python Project", Colors.OKBLUE)
    
    # Verificări preliminare
    if not check_python_version():
        return False
    
    if not check_pip():
        return False
    
    # Creare mediu virtual
    if not create_virtual_environment():
        return False
    
    # Creare directoare
    create_directories()
    
    # Instalare dependințe
    if not install_requirements():
        return False
    
    # Configurare baza de date
    if not setup_database():
        return False
    
    # Creare script-uri de rulare
    create_run_scripts()
    
    # Mesaj finalizare
    show_completion_message()
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print_colored("\n✨ Instalarea s-a finalizat cu succes!", Colors.OKGREEN)
            sys.exit(0)
        else:
            print_colored("\n❌ Instalarea a eșuat!", Colors.FAIL)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_colored("\n\n👋 Instalarea a fost întreruptă de utilizator", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Eroare neașteptată: {e}", Colors.FAIL)
        sys.exit(1)
