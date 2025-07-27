import sqlite3
import pandas as pd
import os
import sys

class CandidatsDB:
    def __init__(self):
        """Initialise la base de données"""
        # Obtenir le chemin absolu du répertoire contenant ce fichier
        if getattr(sys, 'frozen', False):
            # Si l'application est compilée avec PyInstaller
            base_dir = os.path.dirname(sys.executable)
            db_dir = os.path.join(base_dir, 'database')
        else:
            # En mode développement
            db_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.db_path = os.path.join(db_dir, 'candidats.db')
        
        # S'assurer que le répertoire existe
        os.makedirs(db_dir, exist_ok=True)
        
        # Créer la base de données si elle n'existe pas
        if not os.path.exists(self.db_path):
            self.create_tables()
        
        # Créer ou vérifier la base de données
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Vérifier si la table existe
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='candidats'")
                table_count = cursor.fetchone()[0]
                if table_count == 0:
                    self.create_tables()
                    print("Base de données des candidats créée avec succès")
        except sqlite3.Error as e:
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.create_tables()
        
    def reinitialiser_db(self):
        """Réinitialise la base de données lors d'une nouvelle importation"""
        try:
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DROP TABLE IF EXISTS candidats')
                    self.create_tables()
        except Exception as e:
            print(f"Erreur lors de la réinitialisation de la base de données: {e}")

    def create_tables(self):
        """Crée la table des candidats si elle n'existe pas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Créer la table avec IF NOT EXISTS
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS candidats (
                    Code TEXT PRIMARY KEY,
                    FirstName TEXT NOT NULL,
                    LastName TEXT NOT NULL,
                    Cin TEXT,
                    DateNaissance TEXT,
                    TypeBac TEXT,
                    Genre TEXT,
                    LieuNaissance TEXT,
                    Annee TEXT,
                    MoyContCon REAL,
                    MoyGenerale REAL,
                    MoyNationale REAL,
                    MoyRegional REAL,
                    Score REAL,
                    VersionEspace TEXT,
                    region TEXT,
                    province TEXT,
                    espace TEXT,
                    langues TEXT,
                    centreExamen TEXT,
                    gestionnaire TEXT,
                    serieBac TEXT
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la table candidats: {e}")
            # Créer un nouveau fichier de base de données si erreur
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.create_tables()

    def check_duplicate_codes(self, df):
        """Vérifie s'il y a des codes en double dans le DataFrame"""
        duplicates = df[df.duplicated(['Code'], keep=False)]
        if not duplicates.empty:
            duplicate_codes = duplicates['Code'].unique()
            error_details = []
            for code in duplicate_codes:
                rows = duplicates[duplicates['Code'] == code]
                candidates = [f"{row['FirstName']} {row['LastName']}" for _, row in rows.iterrows()]
                error_details.append(f"Code {code} utilisé plusieurs fois pour : {', '.join(candidates)}")
            raise ValueError("Codes en double détectés :\n" + "\n".join(error_details))

    def save_candidats(self, df):
        try:
            # S'assurer que la table existe
            self.create_tables()
            
            # Vérifier que les colonnes requises sont présentes
            required_columns = ["Code", "FirstName", "LastName", "Cin", "DateNaissance", 
                            "TypeBac", "Genre", "LieuNaissance", "Annee", "MoyContCon",
                            "MoyGenerale", "MoyNationale", "MoyRegional", "Score",
                            "VersionEspace", "region", "province", "espace", "langues",
                            "centreExamen", "gestionnaire", "serieBac"]
            
            # Nettoyer les données avant la sauvegarde
            df = df.copy()
            for col in df.columns:
                if col in required_columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].fillna('')
                    else:
                        df[col] = df[col].fillna(0)
            
            # Vérifier les codes en double avant de faire quoi que ce soit
            self.check_duplicate_codes(df)
            
            # Vérifier les colonnes manquantes
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Colonnes manquantes dans le fichier: {', '.join(missing_cols)}")
            
            # Supprimer les doublons basés sur le Code
            initial_count = len(df)
            df = df.drop_duplicates(subset=['Code'], keep='first')
            duplicates_removed = initial_count - len(df)
            if duplicates_removed > 0:
                print(f"Info: {duplicates_removed} doublons de Code ont été supprimés")
            
            # Convertir les types de données
            numeric_cols = ['MoyContCon', 'MoyGenerale', 'MoyNationale', 'MoyRegional', 'Score']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            text_cols = [col for col in required_columns if col not in numeric_cols]
            for col in text_cols:
                df[col] = df[col].astype(str)

            # Se connecter à la base de données
            success_count = 0
            error_count = 0
            errors = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Sauvegarder les données ligne par ligne avec gestion des erreurs
                for index, row in df.iterrows():
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO candidats (
                                Code, FirstName, LastName, Cin, DateNaissance,
                                TypeBac, Genre, LieuNaissance, Annee, MoyContCon,
                                MoyGenerale, MoyNationale, MoyRegional, Score,
                                VersionEspace, region, province, espace, langues,
                                centreExamen, gestionnaire, serieBac
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', tuple(row[col] for col in required_columns))
                        success_count += 1
                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint" in str(e):
                            error_msg = f"Le Code '{row['Code']}' existe déjà dans la base de données"
                        else:
                            error_msg = str(e)
                        errors.append(f"Ligne {index + 2}: {error_msg}")
                        error_count += 1
                    except Exception as e:
                        errors.append(f"Ligne {index + 2}: {str(e)}")
                        error_count += 1
                
                # Valider les changements seulement si tout s'est bien passé
                if error_count == 0:
                    conn.commit()
                    print(f"Importation terminée: {success_count} candidats importés avec succès")
                else:
                    conn.rollback()
                    error_summary = "\n".join(errors[:10])  # Limiter à 10 erreurs pour la lisibilité
                    if len(errors) > 10:
                        error_summary += f"\n... et {len(errors) - 10} autres erreurs"
                    raise ValueError(f"Des erreurs sont survenues lors de l'importation:\n{error_summary}")

        except Exception as e:
            error_msg = f"Erreur lors de la sauvegarde: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)

    def get_all_candidats(self):
        """Récupère tous les candidats de la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query('SELECT * FROM candidats', conn)

    def get_candidat_by_code(self, code):
        """Récupère un candidat par son code"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query('SELECT * FROM candidats WHERE Code = ?', conn, params=(code,))

    def get_candidats_by_centre(self, centre):
        """Récupère tous les candidats d'un centre d'examen"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query('SELECT * FROM candidats WHERE centreExamen = ?', conn, params=(centre,))

    def get_stats(self):
        """Récupère des statistiques sur les candidats"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            stats = {}
            
            try:
                # Vérifier si la table existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidats'")
                if not cursor.fetchone():
                    self.create_tables()
                    return {"total_candidats": 0, "repartition_genre": {}, "moyenne_score": 0}
                
                # Nombre total de candidats
                cursor.execute('SELECT COUNT(*) FROM candidats')
                stats['total_candidats'] = cursor.fetchone()[0]
                
                # Répartition par genre
                cursor.execute('SELECT Genre, COUNT(*) FROM candidats GROUP BY Genre')
                stats['repartition_genre'] = dict(cursor.fetchall())
                
                # Moyenne des scores
                cursor.execute('SELECT AVG(Score) FROM candidats')
                stats['moyenne_score'] = cursor.fetchone()[0]
                
                # Vérifier l'intégrité des données
                if stats['total_candidats'] == 0:
                    print("Attention: Aucun candidat trouvé dans la base de données")
                
            except sqlite3.Error as e:
                print(f"Erreur lors de la récupération des statistiques: {e}")
                stats = {"total_candidats": 0, "repartition_genre": {}, "moyenne_score": 0}
            
            return stats

    def clear_all_candidats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM candidats')
            conn.commit()
