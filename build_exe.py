import os
import shutil
import sys
import subprocess
import PyInstaller.__main__

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    required_packages = [
        'reportlab',
        'pillow',
        'pandas',
        'numpy',
        'openpyxl',
        'PyQt6'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} est installé")
        except ImportError:
            print(f"Installation de {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_icon():
    """Vérifie si l'icône existe"""
    icon_path = os.path.join("assets", "iconapp_512.png")
    if os.path.exists(icon_path):
        print(f"Icône trouvée : {icon_path}")
        return icon_path
    else:
        print("Attention : Icône non trouvée !")
        return None

def setup_database_files():
    """Prépare les fichiers de base de données pour le build"""
    try:
        # S'assurer que le répertoire database existe dans le projet
        os.makedirs("database", exist_ok=True)
        
        # Initialiser les bases de données source
        from database.candidats_db import CandidatsDB
        from database.salles_db import SallesDB
        
        # Créer les bases vides dans le dossier source
        candidats_db = CandidatsDB()
        candidats_db.create_tables()
        
        salles_db = SallesDB()
        salles_db.create_tables()
        
        # Créer le répertoire database dans le répertoire dist
        dist_db_dir = os.path.join("dist", "database")
        os.makedirs(dist_db_dir, exist_ok=True)
        
        # Copier les fichiers Python
        py_files = ['__init__.py', 'candidats_db.py', 'salles_db.py', 'repartition_db.py']
        for py_file in py_files:
            src = os.path.join("database", py_file)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dist_db_dir, py_file))
                print(f"Fichier Python copié : {py_file}")
        
        # Copier les bases de données existantes
        db_files = ['candidats.db', 'salles.db']
        for db_file in db_files:
            src = os.path.join("database", db_file)
            if os.path.exists(src):
                # Copier vers le dossier dist/database
                dst_dist = os.path.join(dist_db_dir, db_file)
                shutil.copy2(src, dst_dist)
                print(f"Base de données copiée : {db_file}")
                
        # Ajouter les fichiers à PyInstaller
        datas = [
            ('database/*.db', 'database'),
            ('database/*.py', 'database'),
        ]
        
        print("Les bases de données ont été préparées pour le build")
    except Exception as e:
        print(f"Erreur lors de la préparation des fichiers de base de données : {e}")

if __name__ == "__main__":
    # Vérifier l'icône
    icon_path = check_icon()
    
    # Préparer les fichiers de base de données
    setup_database_files()
    
    # Configuration pour PyInstaller
    app_name = "ConMedPartApp"
    main_script = "main.py"
    
    # Définir les dossiers source et destination
    current_dir = os.path.dirname(os.path.abspath(__file__))
    database_dir = os.path.join(current_dir, 'database')
    dist_dir = os.path.join(current_dir, 'dist', app_name)
    
    # Options de base
    options = [
        main_script,
        '--name=' + app_name,
        '--noconsole',
        '--clean',
        '--onedir',  # Créer un dossier contenant l'exécutable et les ressources
    ]
    
    # Ajouter l'icône si elle existe
    if icon_path:
        options.append('--icon=' + icon_path)
    
    # Ajouter les données (utiliser des chemins absolus)
    options.extend([
        '--add-data', f'{database_dir}/*.db{os.pathsep}database',
        '--add-data', f'{database_dir}/*.py{os.pathsep}database',
        '--add-data', 'assets/*;assets'
    ])
    
    # Lancer PyInstaller
    PyInstaller.__main__.run(options)
    
    # Après la création de l'exécutable, copier les bases de données
    os.makedirs(os.path.join(dist_dir, 'database'), exist_ok=True)
    for db_file in ['candidats.db', 'salles.db']:
        src = os.path.join(database_dir, db_file)
        if os.path.exists(src):
            dst = os.path.join(dist_dir, 'database', db_file)
            shutil.copy2(src, dst)
            print(f"Base de données copiée vers dist : {db_file}")
    
    print("Build terminé. L'application est prête dans le dossier dist.")
    
    # Options pour PyInstaller
    options = [
        '--name=ConMedPartApp',
        '--windowed',
        '--onefile',
        '--clean',
        '--add-data=assets/*;assets/',
        '--add-data=database/*.py;database/',
        '--add-data=database/*.db;database/',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.pdfbase',
        '--hidden-import=reportlab.pdfbase.ttfonts',
        '--hidden-import=reportlab.platypus',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.lib.pagesizes',
        '--hidden-import=reportlab.lib.units',
        '--hidden-import=reportlab.lib.utils',
        '--hidden-import=reportlab.lib.styles',
        '--hidden-import=PIL',
        '--hidden-import=PIL._imaging',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=openpyxl',
        '--hidden-import=sqlite3',
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets'
    ]
    
    # Ajouter l'icône si elle existe
    if icon_path:
        options.append(f'--icon={icon_path}')
    
    # Ajouter le fichier principal
    options.append('main.py')
    
    # Lancer PyInstaller
    PyInstaller.__main__.run(options)
    
    os.system("python build_exe.py")