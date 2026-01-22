#!/usr/bin/env python3
"""
Script pentru crearea executabilului Medical PACS pe Windows
Versiunea imbunatatita care include assets din app/assets/
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Configurare
APP_NAME = "MediCore-PACS"
APP_VERSION = "2.0.0"
MAIN_SCRIPT = "app/main.py"

def install_pyinstaller():
    """Instaleaza PyInstaller daca nu este gasit"""
    print("Instaland PyInstaller...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("PyInstaller instalat cu succes!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Eroare la instalarea PyInstaller: {e}")
        return False

def check_dependencies():
    """Verifica si instaleaza dependintele daca lipsesc"""
    print("Verificand dependintele...")
    
    required_packages = {
        'pyinstaller': 'pyinstaller',
        'PyQt6': 'PyQt6',
        'sqlalchemy': 'sqlalchemy',
        'pymysql': 'pymysql',
        'bcrypt': 'bcrypt',
        'pydicom': 'pydicom',
        'weasyprint': 'weasyprint',
        'PIL': 'Pillow',
        'requests': 'requests',
        # OpenTelemetry packages (best-effort checks)
        'opentelemetry': 'opentelemetry-api',
        'opentelemetry.sdk': 'opentelemetry-sdk',
        'opentelemetry.exporter.otlp': 'opentelemetry-exporter-otlp',
        'opentelemetry.instrumentation.requests': 'opentelemetry-instrumentation-requests',
        'opentelemetry.instrumentation.sqlalchemy': 'opentelemetry-instrumentation-sqlalchemy',
        'opentelemetry.instrumentation.logging': 'opentelemetry-instrumentation-logging'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"{package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"{package_name} - LIPSESTE")
    
    # Instalează pachetele lipsă
    if missing_packages:
        print(f"\nInstaland pachetele lipsa: {', '.join(missing_packages)}")
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
            subprocess.run(cmd, check=True)
            print("Toate pachetele au fost instalate!")
        except subprocess.CalledProcessError as e:
            print(f"Eroare la instalarea pachetelor: {e}")
            return False
    
    # Verificare specială pentru PyInstaller
    try:
        import PyInstaller
        print("PyInstaller disponibil prin import")
    except ImportError:
        print("PyInstaller nu poate fi importat, instalez...")
        if not install_pyinstaller():
            return False
    
    # Testează comanda pyinstaller
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"PyInstaller versiune: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Comanda pyinstaller nu functioneaza, incerc sa o fix...")
        if not install_pyinstaller():
            return False
    
    print("Toate dependintele sunt OK!")
    return True

def verify_assets():
    """Verifica daca fisierele assets exista"""
    print("\nVerificare assets...")
    
    assets_dir = "app/assets"
    if not os.path.exists(assets_dir):
        print(f"Directorul assets nu exista: {assets_dir}")
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
            print(f"Gasit: {rel_path}")
    
    if not found_files:
        print("Nu s-au gasit fisiere in directorul assets")
    else:
        print(f"Gasite {len(found_files)} fisiere assets")
    
    return True

def clean_build():
    """Curata build-urile anterioare"""
    print("\nCuratand build-urile anterioare...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Sters: {dir_name}")
    
    # Șterge fișierele .spec
    for file in Path(".").glob("*.spec"):
        file.unlink()
        print(f"Sters: {file}")
    
    # Curăță cache Python recursiv
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name))
                dirs.remove(dir_name)
    
    print("Curatarea completa!")

def run_pyinstaller_direct():
    """Ruleaza PyInstaller direct cu parametrii in linia de comanda"""
    print("\nCreand executabilul cu PyInstaller...")
    
    # Verifică dacă avem icon pentru aplicație
    icon_path = None
    possible_icons = ["app/assets/icon.ico", "app/assets/app_icon.ico", "icon.ico"]
    for icon in possible_icons:
        if os.path.exists(icon):
            icon_path = icon
            print(f"Folosesc icon: {icon_path}")
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
        # OpenTelemetry hidden imports (help PyInstaller find exporters/instrumentation)
        "--hidden-import", "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
        "--hidden-import", "opentelemetry.instrumentation.requests",
        "--hidden-import", "opentelemetry.instrumentation.sqlalchemy",
        "--hidden-import", "opentelemetry.instrumentation.logging",
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
    
    print("Comanda PyInstaller:")
    print(" ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller terminat cu succes!")
        if result.stdout:
            print("Output:")
            print(result.stdout[-500:])  # Ultimele 500 caractere
        return True
    except subprocess.CalledProcessError as e:
        print("Eroare la PyInstaller!")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout[-500:])
        if e.stderr:
            print("STDERR:", e.stderr[-500:])
        return False

def verify_executable():
    """Verifica daca executabilul a fost creat si functioneaza"""
    exe_path = f"dist/{APP_NAME}.exe"
    
    if not os.path.exists(exe_path):
        print(f"Executabilul nu a fost gasit: {exe_path}")
        return False
    
    # Verifică dimensiunea
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"Dimensiune executabil: {size_mb:.1f} MB")
    
    if size_mb < 80:  # Un executabil PyQt6 cu WeasyPrint ar trebui să fie > 80MB
        print("Executabilul pare prea mic, possibil lipsesc dependinte")
    else:
        print("Dimensiunea executabilului pare OK")
    
    return True



def create_release_package():
    """Creeaza pachetul final pentru distributie"""
    print("\nCreand pachetul de distributie...")
    
    exe_path = f"dist/{APP_NAME}.exe"
    if not os.path.exists(exe_path):
        print(f"Executabilul nu a fost gasit: {exe_path}")
        return False
    
    # Creează directorul de release
    release_dir = f"release/{APP_NAME}-v{APP_VERSION}"
    os.makedirs(release_dir, exist_ok=True)
    
    # Copiază executabilul
    shutil.copy2(exe_path, release_dir)
    print(f"Executabil copiat in {release_dir}")
    
    # Creează directoarele necesare pentru runtime
    runtime_dirs = [
        "generated_pdfs",
        "tmp_pdfs", 
        "local_studies_cache"
    ]
    
    for dir_name in runtime_dirs:
        os.makedirs(f"{release_dir}/{dir_name}", exist_ok=True)
        print(f"Director creat: {dir_name}")
    
    # Copiază documentația
    docs_to_copy = [
        ("README.txt", "README.txt"),
        ("database_init.py", "database_init.py"),
        ("test_assets.py", "test_assets.py")
    ]
    
    for src, dst in docs_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, f"{release_dir}/{dst}")
            print(f"Copiat: {src}")
    
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
        print(f"Arhiva creata: release/{archive_name}.zip ({archive_size:.1f} MB)")
    
    return True

def create_assets_test_script(release_dir):
    """Creeaza script pentru testarea assets-urilor"""
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

