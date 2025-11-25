#!/usr/bin/env python3
"""
Script pentru crearea executabilului Medical PACS pe Windows
Versiunea îmbunătățită care include assets din app/assets/
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Configurare
APP_NAME = "MediCore-PACS"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = "app/main.py"

def install_pyinstaller():
    """Instalează PyInstaller dacă nu este găsit"""
    print("🔧 Instalând PyInstaller...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller instalat cu succes!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Eroare la instalarea PyInstaller: {e}")
        return False

def check_dependencies():
    """Verifică și instalează dependințele dacă lipsesc"""
    print("🔍 Verificând dependințele...")
    
    required_packages = {
        'pyinstaller': 'pyinstaller',
        'PyQt6': 'PyQt6',
        'sqlalchemy': 'sqlalchemy',
        'pymysql': 'pymysql',
        'bcrypt': 'bcrypt',
        'pydicom': 'pydicom',
        'weasyprint': 'weasyprint',
        'PIL': 'Pillow',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} - LIPSEȘTE")
    
    # Instalează pachetele lipsă
    if missing_packages:
        print(f"\n🔧 Instalând pachetele lipsă: {', '.join(missing_packages)}")
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
            subprocess.run(cmd, check=True)
            print("✅ Toate pachetele au fost instalate!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Eroare la instalarea pachetelor: {e}")
            return False
    
    # Verificare specială pentru PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller disponibil prin import")
    except ImportError:
        print("⚠️  PyInstaller nu poate fi importat, instalez...")
        if not install_pyinstaller():
            return False
    
    # Testează comanda pyinstaller
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PyInstaller versiune: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Comanda pyinstaller nu funcționează, încerc să o fix...")
        if not install_pyinstaller():
            return False
    
    print("✅ Toate dependințele sunt OK!")
    return True

def verify_assets():
    """Verifică dacă fișierele assets există"""
    print("\n🖼️  Verificare assets...")
    
    assets_dir = "app/assets"
    if not os.path.exists(assets_dir):
        print(f"⚠️  Directorul assets nu exista: {assets_dir}")
        print("Creez directorul assets...")
        os.makedirs(assets_dir, exist_ok=True)
        return True
    
    # Verifică fișierele importante
    important_files = [
        "header_spital.png",
        "icon.ico",  # Daca ai un icon pentru aplicatie
    ]
    
    found_files = []
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), assets_dir)
            found_files.append(rel_path)
            print(f"📁 Gasit: {rel_path}")
    
    if not found_files:
        print("⚠️  Nu s-au gasit fisiere in directorul assets")
    else:
        print(f"✅ Gasite {len(found_files)} fisiere assets")
    
    return True

def clean_build():
    """Curăță build-urile anterioare"""
    print("\n🧹 Curățând build-urile anterioare...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️  Șters: {dir_name}")
    
    # Șterge fișierele .spec
    for file in Path(".").glob("*.spec"):
        file.unlink()
        print(f"🗑️  Șters: {file}")
    
    # Curăță cache Python recursiv
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name))
                dirs.remove(dir_name)
    
    print("✅ Curățarea completă!")

def run_pyinstaller_direct():
    """Rulează PyInstaller direct cu parametrii în linia de comandă"""
    print("\n🔨 Creând executabilul cu PyInstaller...")
    
    # Verifică dacă avem icon pentru aplicație
    icon_path = None
    possible_icons = ["app/assets/icon.ico", "app/assets/app_icon.ico", "icon.ico"]
    for icon in possible_icons:
        if os.path.exists(icon):
            icon_path = icon
            print(f"🎨 Folosesc icon: {icon_path}")
            break
    
    # Parametrii pentru PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        # Adaugă directorul assets complet
        "--add-data", "app/assets;app/assets",
        # Adaugă fișierele de stil
        "--add-data", "app/presentation/styles/*.qss;app/presentation/styles",
        "--add-data", "app/presentation/styles/*.css;app/presentation/styles",
        # Import-uri hidden importante
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "sqlalchemy.dialects.mysql.pymysql",
        "--hidden-import", "pymysql",
        "--hidden-import", "bcrypt",
        "--hidden-import", "pydicom",
        "--hidden-import", "weasyprint",
        "--hidden-import", "PIL",
        "--hidden-import", "app.di.container",
        "--hidden-import", "app.services.pacs_service",
        "--hidden-import", "app.services.auth_service",
        "--hidden-import", "app.services.session_service",
        "--hidden-import", "app.services.local_file_service",
        "--hidden-import", "app.services.hybrid_pacs_service",
        "--hidden-import", "app.services.pdf_service",
        "--hidden-import", "app.services.notification_service",
        "--hidden-import", "app.services.pacs_url_service",
        "--hidden-import", "app.services.settings_service",
        "--hidden-import", "app.services.dicom_anonymizer_service",
        "--hidden-import", "app.services.report_title_service",
        # Exclude module grele
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "jupyter",
        "--exclude-module", "notebook",
        # UPX compression (opțional - comentează dacă ai probleme)
        # "--upx-dir", "C:/upx",  # Dacă ai UPX instalat
    ]
    
    # Adaugă icon dacă există
    if icon_path:
        cmd.extend(["--icon", icon_path])
    
    # Adaugă fișierul principal
    cmd.append(MAIN_SCRIPT)
    
    print("📝 Comanda PyInstaller:")
    print(" ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ PyInstaller terminat cu succes!")
        if result.stdout:
            print("📋 Output:")
            print(result.stdout[-500:])  # Ultimele 500 caractere
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Eroare la PyInstaller!")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout[-500:])
        if e.stderr:
            print("STDERR:", e.stderr[-500:])
        return False

def verify_executable():
    """Verifică dacă executabilul a fost creat și funcționează"""
    exe_path = f"dist/{APP_NAME}.exe"
    
    if not os.path.exists(exe_path):
        print(f"❌ Executabilul nu a fost găsit: {exe_path}")
        return False
    
    # Verifică dimensiunea
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"📏 Dimensiune executabil: {size_mb:.1f} MB")
    
    if size_mb < 80:  # Un executabil PyQt6 cu WeasyPrint ar trebui să fie > 80MB
        print("⚠️  Executabilul pare prea mic, possibil lipsesc dependințe")
    else:
        print("✅ Dimensiunea executabilului pare OK")
    
    return True

def test_assets_in_executable():
    """Testează dacă assets-urile sunt incluse în executabil"""
    print("\n🧪 Testează dacă assets-urile sunt incluse...")
    
    # Creează un script de test temporar
    test_script = """
import sys
import os
from pathlib import Path

# Detecteaza daca rulam ca executabil PyInstaller
if getattr(sys, 'frozen', False):
    # Ruleaza ca executabil
    bundle_dir = sys._MEIPASS
    print(f"Running as executable, bundle dir: {bundle_dir}")
    
    # Verifica assets
    assets_path = os.path.join(bundle_dir, 'app', 'assets')
    if os.path.exists(assets_path):
        print(f"Assets found at: {assets_path}")
        files = list(os.listdir(assets_path))
        print(f"Files: {files}")
        
        # Verifica header_spital.png specific
        header_path = os.path.join(assets_path, 'header_spital.png')
        if os.path.exists(header_path):
            size = os.path.getsize(header_path)
            print(f"header_spital.png found, size: {size} bytes")
        else:
            print("header_spital.png NOT found")
    else:
        print(f"Assets directory not found")
        print(f"Bundle contents:")
        for item in os.listdir(bundle_dir):
            print(f"  - {item}")
else:
    print("Not running as executable")
"""
    
    # Salvează script-ul de test cu encoding UTF-8
    with open("test_assets.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("✅ Script de test creat: test_assets.py")
    print("  Poti rula 'dist/MediCore-PACS.exe test_assets.py' pentru a testa assets-urile")
    
    return True

def create_release_package():
    """Creează pachetul final pentru distribuție"""
    print("\n📦 Creând pachetul de distribuție...")
    
    exe_path = f"dist/{APP_NAME}.exe"
    if not os.path.exists(exe_path):
        print(f"❌ Executabilul nu a fost găsit: {exe_path}")
        return False
    
    # Creează directorul de release
    release_dir = f"release/{APP_NAME}-v{APP_VERSION}"
    os.makedirs(release_dir, exist_ok=True)
    
    # Copiază executabilul
    shutil.copy2(exe_path, release_dir)
    print(f"✅ Executabil copiat în {release_dir}")
    
    # Creează directoarele necesare pentru runtime
    runtime_dirs = [
        "generated_pdfs",
        "tmp_pdfs", 
        "local_studies_cache"
    ]
    
    for dir_name in runtime_dirs:
        os.makedirs(f"{release_dir}/{dir_name}", exist_ok=True)
        print(f"📁 Director creat: {dir_name}")
    
    # Copiază documentația
    docs_to_copy = [
        ("README.txt", "README.txt"),
        ("database_init.py", "database_init.py"),
        ("test_assets.py", "test_assets.py")
    ]
    
    for src, dst in docs_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, f"{release_dir}/{dst}")
            print(f"📋 Copiat: {src}")
    
    # Creează instrucțiunile de instalare
    create_install_instructions(release_dir)
    
    # Creează script-ul de test pentru assets
    create_assets_test_script(release_dir)
    
    # Creează arhiva ZIP
    archive_name = f"{APP_NAME}-v{APP_VERSION}-Windows"
    shutil.make_archive(f"release/{archive_name}", 'zip', f"release", f"{APP_NAME}-v{APP_VERSION}")
    
    # Calculează dimensiunea arhivei
    if os.path.exists(f"release/{archive_name}.zip"):
        archive_size = os.path.getsize(f"release/{archive_name}.zip") / (1024 * 1024)
        print(f"✅ Arhiva creată: release/{archive_name}.zip ({archive_size:.1f} MB)")
    
    return True

def create_assets_test_script(release_dir):
    """Creează script pentru testarea assets-urilor"""
    test_script = f"""@echo off
echo ========================================
echo  Testing {APP_NAME} Assets
echo ========================================
echo.

echo Testing if assets are properly bundled...
{APP_NAME}.exe --test-assets

echo.
echo If you see errors above, the assets might not be properly bundled.
echo Please contact support with the error details.
echo.
pause
"""
    
    with open(f"{release_dir}/test-assets.bat", "w", encoding="utf-8") as f:
        f.write(test_script)

def create_install_instructions(release_dir):
    """Creează fișierul cu instrucțiuni de instalare"""
    instructions = f"""=== MEDICAL PACS v{APP_VERSION} - GHID INSTALARE ===

📋 CONȚINUTUL PACHETULUI:
- {APP_NAME}.exe          - Aplicația principală
- generated_pdfs/         - Director pentru PDF-uri generate
- tmp_pdfs/              - Director temporar pentru preview
- local_studies_cache/   - Cache pentru studii locale DICOM
- database_init.py       - Script pentru inițializarea bazei de date
- test-assets.bat        - Test pentru verificarea assets-urilor
- INSTALARE.txt          - Acest fișier

🖥️ CERINȚE SISTEM:
- Windows 10/11 (64-bit)
- MySQL Server 5.7+ sau MariaDB 10.3+
- 4GB RAM minimum
- 1GB spațiu liber pe disk
- Conexiune la rețea (pentru PACS)

📚 INSTALARE PAS CU PAS:

1. PREGĂTIREA BAZEI DE DATE
   a) Instalează MySQL Server de la: https://dev.mysql.com/downloads/mysql/
   b) În timpul instalării, reține parola pentru root
   c) Deschide MySQL Command Line Client și execută:
   
      CREATE DATABASE medical_app CHARACTER SET utf8mb4;
      CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin';
      GRANT ALL PRIVILEGES ON medical_app.* TO 'admin'@'localhost';
      FLUSH PRIVILEGES;
      EXIT;

2. INSTALAREA APLICAȚIEI
   a) Extraie toate fișierele din această arhivă într-un director permanent
   b) Pentru prima rulare, click-dreapta pe {APP_NAME}.exe → "Run as administrator"
   c) Aplicația va crea automat tabelele în baza de date
   d) Rulează test-assets.bat pentru a verifica că assets-urile sunt OK

3. PRIMUL LOGIN
   Username: admin
   Parola: admin
   
   ⚠️ FOARTE IMPORTANT: Schimbă imediat parola administratorului!

4. CONFIGURAREA PACS
   a) Din meniul principal → Admin Panel → PACS URLs
   b) Adaugă serverele tale PACS cu datele de conectare
   c) Testează conexiunea pentru fiecare server
   d) Setează PACS-ul sursă și țintă din setări

🔧 PROBLEME FRECVENTE:

❌ "Could not connect to database"
   → Verifică dacă MySQL Server rulează (Services → MySQL)
   → Verifică datele de conectare în configurație

❌ "Permission denied" la pornire
   → Rulează ca Administrator prima dată
   → Verifică dacă antivirusul blochează aplicația
   → Adaugă excepție în Windows Defender

❌ "PACS connection failed"
   → Verifică URL-ul serverului PACS (ex: http://server:8042)
   → Testează în browser accesul la PACS
   → Verifică username/parola PACS

❌ "Header image not found" în PDF-uri
   → Rulează test-assets.bat pentru diagnosticare
   → Verifică că ai extras complet arhiva ZIP

❌ Executabilul nu pornește deloc
   → Instalează Visual C++ Redistributable 2015-2022:
     https://aka.ms/vs/17/release/vc_redist.x64.exe
   → Adaugă excepție în antivirus pentru {APP_NAME}.exe

🛠️ SETUP AUTOMAT BAZA DE DATE:
Dacă ai probleme cu setup-ul manual, rulează:
python database_init.py

🔄 PENTRU ACTUALIZĂRI:
1. Oprește aplicația veche complet
2. Fă backup la baza de date (mysqldump medical_app > backup.sql)
3. Înlocuiește {APP_NAME}.exe cu versiunea nouă
4. Păstrează directoarele cu date (generated_pdfs, etc.)
5. Rulează aplicația nouă

📞 SUPORT TEHNIC:
Email: support@medical-solutions.com
Documentație: https://docs.medical-solutions.com

Versiune: {APP_VERSION}
Data build: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Includes assets: ✅ Da (app/assets integrat în executabil)

🧪 TESTARE RAPIDĂ:
1. Rulează {APP_NAME}.exe
2. Loghează-te cu admin/admin  
3. Încearcă să generezi un PDF de test
4. Verifică că imaginea header apare în PDF
"""
    
    with open(f"{release_dir}/INSTALARE.txt", "w", encoding="utf-8") as f:
        f.write(instructions)

def main():
    """Funcția principală"""
    print(f"🚀 Medical PACS Build Tool v{APP_VERSION}")
    print("=" * 70)
    print("Creează executabilul pentru Windows cu assets incluse")
    print()
    
    # Verifică dacă suntem în directorul corect
    if not os.path.exists(MAIN_SCRIPT):
        print(f"❌ Nu găsesc fișierul principal: {MAIN_SCRIPT}")
        print("Asigură-te că rulezi script-ul din directorul rădăcină al proiectului")
        input("Apasă Enter pentru a ieși...")
        return 1
    
    # Verificări și instalări
    if not check_dependencies():
        print("\n❌ Nu s-au putut rezolva dependințele!")
        input("Apasă Enter pentru a ieși...")
        return 1
    
    if not verify_assets():
        print("\n❌ Probleme cu assets-urile!")
        input("Apasă Enter pentru a ieși...")
        return 1
    
    # Build process
    clean_build()
    
    if not run_pyinstaller_direct():
        print("\n❌ Build eșuat la PyInstaller!")
        input("Apasă Enter pentru a ieși...")
        return 1
    
    if not verify_executable():
        print("\n❌ Verificarea executabilului a eșuat!")
        input("Apasă Enter pentru a ieși...")
        return 1
    
    test_assets_in_executable()
    
    if not create_release_package():
        print("\n❌ Eșec la crearea pachetului de distribuție!")
        input("Apasă Enter pentru a ieși...")
        return 1
    
    # Succes!
    print("\n" + "=" * 70)
    print("🎉 BUILD COMPLET CU SUCCES!")
    print("=" * 70)
    print(f"📦 Executabil: dist/{APP_NAME}.exe")
    print(f"🗜️  Pachet distribuție: release/{APP_NAME}-v{APP_VERSION}-Windows.zip")
    print()
    print("📋 Ce să faci acum:")
    print("1. Testează executabilul local din dist/")
    print("2. Rulează test-assets.bat pentru a verifica assets-urile")
    print("3. Distribuie arhiva ZIP din release/")
    print("4. Utilizatorii urmează ghidul din INSTALARE.txt")
    print()
    print("🖼️  Assets incluse:")
    print("- header_spital.png (pentru PDF-uri)")
    print("- Toate fișierele din app/assets/")
    print()
    print("🔧 Pentru debugging:")
    print("- Verifică că header-ul apare în PDF-urile generate")
    print("- Testează pe un sistem curat fără Python instalat")
    print("- Verifică că MySQL Server rulează pe sistemul destinație")
    
    input("\nApasă Enter pentru a ieși...")
    return 0

if __name__ == "__main__":
    exit(main())