import sqlite3
import pandas as pd
import os
import openpyxl
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows

# Définitions des constantes
COLUMN_MAPPING = {
    "Centres d'examen": "centre",
    "Locaux d'examen": "nom",
    "Capacité": "capacite",
    "Climatisé": "climatise",
    "Camera": "camera"
}

class SallesDB:
    def __init__(self):
        """Initialise la base de données"""
        # Obtenir le chemin absolu du répertoire contenant ce fichier
        db_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(db_dir, 'salles.db')
        
        # S'assurer que le répertoire existe
        os.makedirs(db_dir, exist_ok=True)
        
        # Créer ou vérifier la base de données
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Vérifier si les tables existent
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('centres', 'salles')")
                table_count = cursor.fetchone()[0]
                if table_count < 2:
                    self.create_tables()
        except sqlite3.Error as e:
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
            # Si la base de données est corrompue, la recréer
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.create_tables()
        
    def add_centre_if_empty(self, nom_centre):
        """Ajoute un centre par défaut si la base est vide"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Vérifier si des centres existent
                cursor.execute("SELECT COUNT(*) FROM centres")
                count = cursor.fetchone()[0]
                if count == 0:
                    # Ajouter un centre par défaut
                    cursor.execute("INSERT INTO centres (nom) VALUES (?)", (nom_centre,))
                    conn.commit()
        except sqlite3.Error as e:
            print(f"Erreur lors de l'ajout du centre par défaut: {e}")

    def reinitialiser_db(self):
        """Réinitialise la base de données lors d'une nouvelle importation"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.create_tables()
        except Exception as e:
            print(f"Erreur lors de la réinitialisation de la base de données: {e}")

    def create_tables(self):
        """Crée les tables si elles n'existent pas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table des centres
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS centres (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nom TEXT UNIQUE NOT NULL
                    )
                ''')
                
                # Table des salles
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS salles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        centre_id INTEGER NOT NULL,
                        nom TEXT NOT NULL,
                        capacite INTEGER NOT NULL,
                        climatise INTEGER NOT NULL DEFAULT 0,
                        camera INTEGER NOT NULL DEFAULT 0,
                        type TEXT NOT NULL DEFAULT 'Grande',
                        FOREIGN KEY (centre_id) REFERENCES centres(id),
                        UNIQUE(centre_id, nom)
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Erreur lors de la création des tables: {e}")
            # Ne pas supprimer la base de données, juste propager l'erreur
            raise

    def save_salles(self, df_salles, excel_path=None):
        """
        Sauvegarde les données des salles depuis un DataFrame
        Args:
            df_salles: DataFrame contenant les données des salles
            excel_path: Chemin vers le fichier Excel d'origine (pour détecter les couleurs)
        """
        try:
            # Sauvegarder le chemin du fichier Excel dans les métadonnées du DataFrame
            if excel_path:
                df_salles._metadata = {'excel_path': excel_path}
                
            # Vérifier que toutes les colonnes requises sont présentes
            required_cols = ["Centres d'examen", "Locaux d'examen", "Capacité", "Climatisé", "Camera"]
            
            # Normaliser les noms de colonnes
            df = df_salles.copy()
            df.columns = df.columns.str.strip()
            
            # Vérifier les colonnes manquantes
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Colonnes manquantes : {', '.join(missing_cols)}")

            # Créer une copie du DataFrame et préparer les données
            df['type'] = 'Grande'  # Par défaut toutes les salles sont grandes
            
            # Détecter les salles en rouge depuis Excel et les marquer comme Petite
            try:
                import openpyxl
                from openpyxl.styles import Font
                from openpyxl.utils.dataframe import dataframe_to_rows
                
                # Récupérer le fichier Excel d'origine
                if hasattr(df_salles, '_metadata') and 'excel_path' in df_salles._metadata:
                    excel_path = df_salles._metadata['excel_path']
                    
                    # Charger le workbook
                    wb = openpyxl.load_workbook(excel_path)
                    ws = wb.active
                    
                    # Trouver l'index de la colonne "Locaux d'examen"
                    header_row = next(ws.rows)
                    col_idx = None
                    for idx, cell in enumerate(header_row):
                        if cell.value == "Locaux d'examen":
                            col_idx = idx
                            break
                    
                    if col_idx is not None:
                        # Pour chaque ligne après l'en-tête
                        for row in list(ws.rows)[1:]:
                            cell = row[col_idx]
                            if cell.font and cell.font.color and cell.font.color.rgb == "FFFF0000":  # Rouge
                                # Trouver cette salle dans notre DataFrame et la marquer comme Petite
                                salle_nom = cell.value
                                if salle_nom:
                                    mask = df["Locaux d'examen"] == salle_nom
                                    df.loc[mask, 'type'] = 'Petite'
            except Exception as e:
                print(f"Attention: Impossible de détecter les couleurs du fichier Excel: {str(e)}")
                print("Les salles seront classifiées uniquement selon leur capacité.")
            
            # Convertir les colonnes
            df['Capacité'] = pd.to_numeric(df['Capacité'], errors='coerce').fillna(0).astype(int)
            df['Climatisé'] = df['Climatisé'].fillna('Non')
            df['Camera'] = df['Camera'].fillna('Non')
            
            # Renommer les colonnes pour la base de données
            df = df.rename(columns={
                "Centres d'examen": "centre",
                "Locaux d'examen": "nom",
                "Capacité": "capacite",
                "Climatisé": "climatise",
                "Camera": "camera"
            })

            # Convertir Oui/Non en 1/0 pour la base de données
            df['climatise'] = df['climatise'].apply(lambda x: 1 if str(x).lower() in ['oui', 'yes', 'true', '1'] else 0)
            df['camera'] = df['camera'].apply(lambda x: 1 if str(x).lower() in ['oui', 'yes', 'true', '1'] else 0)
            
            with sqlite3.connect(self.db_path) as conn:
                # Supprimer les anciennes données
                conn.execute('DELETE FROM salles')
                conn.execute('DELETE FROM sqlite_sequence WHERE name="salles"')
                
                # Insérer les données centre par centre
                centres_ids = {}
                
                for centre_name in df['centre'].unique():
                    # Insérer le centre
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO centres (nom) VALUES (?)', (centre_name,))
                    centre_id = cursor.lastrowid
                    centres_ids[centre_name] = centre_id
                    
                    # Insérer les salles de ce centre
                    centre_df = df[df['centre'] == centre_name].copy()
                    centre_df['centre_id'] = centre_id
                    centre_df = centre_df[['centre_id', 'nom', 'capacite', 'climatise', 'camera', 'type']]
                    centre_df.to_sql('salles', conn, if_exists='append', index=False)
                
            return True, "Données sauvegardées avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde : {str(e)}"# Remplacer les caractères mal encodés connus
            replacements = {
                'ú': 'é',
                'Ú': 'é',
                'è': 'e',
                'à': 'a',
                'â': 'a'
            }
            col = col.strip()
            for old, new in replacements.items():
                col = col.replace(old, new)
            return col
        
        # Appliquer la normalisation aux noms de colonnes
        df.columns = [normalize_column_name(col) for col in df.columns]
        
        print("Noms de colonnes après correction d'encodage:", df.columns.tolist())
        
        # Mapping des noms de colonnes possibles (avec toutes les variations possibles)
        column_mapping = {
            'centres d\'examen': "Centres d'examen",
            'centre d\'examen': "Centres d'examen",
            'centre': "Centres d'examen",
            'centres': "Centres d'examen",
            'locaux d\'examen': "Locaux d'examen",
            'local d\'examen': "Locaux d'examen",
            'locaux': "Locaux d'examen",
            'local': "Locaux d'examen",
            'nom': "Locaux d'examen",
            'salle': "Locaux d'examen",
            'capacité': "Capacité",
            'capacite': "Capacité",
            'cap': "Capacité",
            'climatisé': "Climatisé",
            'climatise': "Climatisé",
            'clim': "Climatisé",
            'camera': "Camera",
            'caméra': "Camera",
            'cam': "Camera",
            'type': "Type",
            'type de salle': "Type"
        }
        
        # Renommer les colonnes si nécessaire avec gestion des variations
        for old_col in df.columns:
            # Normaliser le nom de la colonne pour la comparaison
            normalized_col = old_col.lower().strip()
            normalized_col = ''.join(c for c in normalized_col if c.isalnum() or c in ["'", " "])
            
            # Chercher la meilleure correspondance dans le mapping
            for key in column_mapping:
                if key in normalized_col or normalized_col in key:
                    df = df.rename(columns={old_col: column_mapping[key]})
                    break
        
        print("Colonnes après normalisation:", df.columns.tolist())
        
        # Vérifier les colonnes requises
        colonnes_requises = [
            "Centres d'examen",
            "Locaux d'examen",
            "Capacité",
            "Climatisé",
            "Camera",
            "Type"
        ]
        
        colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]
        if colonnes_manquantes:
            raise ValueError(f"Colonnes manquantes dans le fichier : {', '.join(colonnes_manquantes)}")
        
        # Nettoyer les données
        df = df.fillna('')
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip().replace({'nan': '', 'None': '', 'NaN': '', 'none': ''})
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Commencer une transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Vider les tables existantes
                cursor.execute("DELETE FROM salles")
                cursor.execute("DELETE FROM centres")
                
                # Réinitialiser les séquences
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('centres', 'salles')")
                
                # Garder une trace des centres pour éviter les duplications
                centres_ids = {}
                
                for index, row in df.iterrows():
                    # Vérifier et nettoyer le nom du centre
                    centre_name = str(row["Centres d'examen"]).strip()
                    if not centre_name:
                        print(f"Ligne {index + 2}: Centre manquant, ignoré")
                        continue
                    
                    # Vérifier et nettoyer le nom de la salle
                    local_name = str(row["Locaux d'examen"]).strip()
                    if not local_name:
                        print(f"Ligne {index + 2}: Local d'examen manquant pour le centre '{centre_name}', ignoré")
                        continue
                        
                    print(f"Traitement de la salle '{local_name}' du centre '{centre_name}'")
                        
                    # Vérifier si le centre existe déjà
                    if centre_name in centres_ids:
                        centre_id = centres_ids[centre_name]
                    else:
                        cursor.execute('INSERT INTO centres (nom) VALUES (?)', (centre_name,))
                        centre_id = cursor.lastrowid
                        centres_ids[centre_name] = centre_id
                    
                    # Convertir la capacité en entier
                    try:
                        capacite_str = str(row['Capacité']).strip()
                        if not capacite_str:
                            print(f"Ligne {index + 2}: Capacité manquante pour la salle '{local_name}' du centre '{centre_name}', ignoré")
                            continue
                            
                        capacite = int(float(capacite_str))
                        if capacite < 0:
                            print(f"Ligne {index + 2}: Capacité négative ({capacite}) pour la salle '{local_name}' du centre '{centre_name}', ignoré")
                            continue
                    except (ValueError, TypeError):
                        print(f"Ligne {index + 2}: Capacité invalide '{capacite_str}' pour la salle '{local_name}' du centre '{centre_name}', ignoré")
                        continue
                    
                    # Traiter les valeurs pour climatisé et caméra
                    climatise_val = str(row['Climatisé']).lower()
                    climatise = 1 if climatise_val in ['1', 'true', 'oui', 'yes', 'o', 'y'] else 0
                    
                    camera_val = str(row['Camera']).lower()
                    camera = 1 if camera_val in ['1', 'true', 'oui', 'yes', 'o', 'y'] else 0
                    
                    # Récupérer et valider le type de la salle
                    type_salle = str(row['Type']).strip()
                    if not type_salle or type_salle.lower() not in ['grande', 'petite']:
                        type_salle = 'Grande'
                        # En cas d'erreur, on garde le type 'Grande' par défaut
                    
                    try:
                        # Insérer la salle
                        cursor.execute('''
                            INSERT INTO salles 
                            (centre_id, nom, capacite, climatise, camera, type)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            centre_id,
                            local_name,
                            capacite,
                            climatise,
                            camera,
                            type_salle
                        ))
                    except sqlite3.IntegrityError as e:
                        print(f"Erreur: La salle '{local_name}' existe déjà dans le centre '{centre_name}'")
                        continue
                
                # Valider la transaction
                cursor.execute("COMMIT")
                
            except Exception as e:
                # En cas d'erreur, annuler toutes les modifications
                cursor.execute("ROLLBACK")
                print(f"Erreur lors de la sauvegarde des données: {str(e)}")
                raise e

    def get_all_salles(self):
        """
        Récupère toutes les salles avec leurs informations dans l'ordre d'origine
        """
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT 
                    c.nom as "Centres d'examen",
                    s.nom as "Locaux d'examen",
                    s.capacite as "Capacité",
                    s.climatise as "Climatisé",
                    s.camera as "Camera",
                    COALESCE(s.type, 'Grande') as type,
                    s.id as id
                FROM salles s
                JOIN centres c ON s.centre_id = c.id
                ORDER BY 
                    s.id ASC
            '''
            df = pd.read_sql_query(query, conn)
            
            # Nettoyer et formater les données
            df = df.fillna('')
            
            # Convertir les types de données
            df['Capacité'] = pd.to_numeric(df['Capacité'], errors='coerce').fillna(0).astype(int)
            df['Climatisé'] = df['Climatisé'].astype(str)
            df['Camera'] = df['Camera'].astype(str)
            df['type'] = df['type'].apply(lambda x: x if str(x).strip() in ['Grande', 'Petite'] else 'Grande')
            
            # Nettoyer les chaînes de caractères
            df['Locaux d\'examen'] = df['Locaux d\'examen'].str.strip()
            df['Centres d\'examen'] = df['Centres d\'examen'].str.strip()
            
            # Remplacer les valeurs NaN/None
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).replace('nan', '')
            
            # Trier par ID pour maintenir l'ordre d'origine
            df = df.sort_values('id')
            
            return df

    def get_all_centres(self):
        """Récupère tous les centres"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query('SELECT * FROM centres', conn)

    def get_salles_by_centre(self, centre_id):
        """Récupère toutes les salles d'un centre"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query('''
                SELECT 
                    s.nom as "Locaux d'examen",
                    s.capacite as "Capacité",
                    s.climatise as "Climatisé",
                    s.camera as "Camera",
                    s.type as "Type"
                FROM salles s
                JOIN centres c ON s.centre_id = c.id
                WHERE c.id = ?
                ORDER BY s.id ASC
            ''', conn, params=(centre_id,))

    def get_salle_details(self, salle_id):
        """Récupère les détails d'une salle"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query('''
                SELECT s.*, c.nom as centre_nom
                FROM salles s
                JOIN centres c ON s.centre_id = c.id
                WHERE s.id = ?
            ''', conn, params=(salle_id,))

    def get_capacite_totale(self):
        """Calcule la capacité totale de toutes les salles"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    SUM(capacite) as total,
                    SUM(CASE WHEN type = 'Grande' THEN capacite ELSE 0 END) as total_grandes,
                    SUM(CASE WHEN type = 'Petite' THEN capacite ELSE 0 END) as total_petites
                FROM salles
            ''')
            return cursor.fetchone()

    def get_stats_by_centre(self):
        """
        Récupère les statistiques par centre
        """
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT 
                    c.nom as centre,
                    COUNT(*) as nb_salles,
                    SUM(capacite) as capacite_totale,
                    SUM(CASE WHEN type = 'Grande' THEN capacite ELSE 0 END) as capacite_grandes_salles,
                    SUM(CASE WHEN climatise = 1 THEN 1 ELSE 0 END) as nb_climatisees,
                    SUM(CASE WHEN camera = 1 THEN 1 ELSE 0 END) as nb_cameras
                FROM salles s
                JOIN centres c ON s.centre_id = c.id
                GROUP BY c.id, c.nom
            '''
            return pd.read_sql_query(query, conn)

    def get_stats_salles(self):
        """Récupère des statistiques sur les salles"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            stats = {}
            
            # Nombre total de salles
            cursor.execute('SELECT COUNT(*) FROM salles')
            stats['total_salles'] = cursor.fetchone()[0]
            
            # Nombre de salles par type
            cursor.execute('SELECT type, COUNT(*) FROM salles GROUP BY type')
            stats['salles_par_type'] = dict(cursor.fetchall())
            
            # Nombre de salles climatisées
            cursor.execute('SELECT COUNT(*) FROM salles WHERE climatise = 1')
            stats['salles_climatisees'] = cursor.fetchone()[0]
            
            # Nombre de salles avec caméras
            cursor.execute('SELECT COUNT(*) FROM salles WHERE camera = 1')
            stats['salles_avec_cameras'] = cursor.fetchone()[0]
            
            return stats

    def add_salle(self, centre, nom, capacite, climatise, camera, type='Grande'):
        """
        Ajoute une nouvelle salle
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Vérifier si le centre existe, sinon le créer
            cursor.execute('SELECT id FROM centres WHERE nom = ?', (centre,))
            result = cursor.fetchone()
            
            if result:
                centre_id = result[0]
            else:
                cursor.execute('INSERT INTO centres (nom) VALUES (?)', (centre,))
                centre_id = cursor.lastrowid
            
            # Ajouter la salle
            cursor.execute('''
                INSERT INTO salles (centre_id, nom, capacite, climatise, camera, type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (centre_id, nom, capacite, climatise, camera, type))
            
            conn.commit()

    def update_salle(self, centre, ancien_nom, nouveau_nom, capacite, climatise, camera, type='Grande'):
        """
        Met à jour les informations d'une salle existante
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Trouver l'ID du centre
            cursor.execute('SELECT id FROM centres WHERE nom = ?', (centre,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Centre '{centre}' non trouvé")
            
            centre_id = result[0]
            
            # Mettre à jour la salle
            cursor.execute('''
                UPDATE salles 
                SET nom = ?, capacite = ?, climatise = ?, camera = ?, type = ?
                WHERE centre_id = ? AND nom = ?
            ''', (nouveau_nom, capacite, climatise, camera, type, centre_id, ancien_nom))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Salle '{ancien_nom}' non trouvée dans le centre '{centre}'")
            
            conn.commit()

    def delete_salle(self, centre, nom):
        """
        Supprime une salle
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Trouver l'ID du centre
            cursor.execute('SELECT id FROM centres WHERE nom = ?', (centre,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Centre '{centre}' non trouvé")
            
            centre_id = result[0]
            
            # Supprimer la salle
            cursor.execute('DELETE FROM salles WHERE centre_id = ? AND nom = ?', (centre_id, nom))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Salle '{nom}' non trouvée dans le centre '{centre}'")
            
            # Si c'était la dernière salle du centre, supprimer le centre aussi
            cursor.execute('SELECT COUNT(*) FROM salles WHERE centre_id = ?', (centre_id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('DELETE FROM centres WHERE id = ?', (centre_id,))
            
            conn.commit()
