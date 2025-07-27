import sqlite3
import pandas as pd
import os

def get_db_path(filename):
    """Retourne le chemin absolu vers le fichier de base de données"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, filename)

class RepartitionDB:
    def __init__(self):
        """Initialise la connexion à la base de données"""
       
        self.db_path = get_db_path('repartition.db')
        self.create_table()
    
    def create_table(self):
        """Crée la table repartition si elle n'existe pas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS repartition (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT NOT NULL,
                        lastname TEXT NOT NULL,
                        firstname TEXT NOT NULL,
                        region TEXT NOT NULL,
                        province TEXT NOT NULL,
                        centre TEXT NOT NULL,
                        salle TEXT NOT NULL,
                        numplace INTEGER NOT NULL,
                        langues TEXT,
                        mode_repartition TEXT ,
                        date_repartition TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la table: {e}")
            raise
    
    def save_repartition(self, resultats_df, mode_repartition='ALEATOIRE'):
        """
        Sauvegarde une nouvelle répartition dans la base de données.
        Supprime d'abord les anciennes données avant d'insérer les nouvelles.
        :param resultats_df: DataFrame contenant les données de répartition
        :param mode_repartition: Mode de répartition ('ALEATOIRE' ou 'PRIORITAIRE')
        """
        # S'assurer que le mode est en majuscules et valide
        mode_repartition = str(mode_repartition).upper()
        if mode_repartition not in ['ALEATOIRE', 'PRIORITAIRE']:
            raise ValueError("Le mode de répartition doit être 'ALEATOIRE' ou 'PRIORITAIRE'")
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Supprimer les anciennes données
                cursor = conn.cursor()
                cursor.execute("DELETE FROM repartition")
                
                # Préparer les données pour l'insertion
                data = resultats_df[[
                    'Code', 'LastName', 'FirstName', 'region', 
                    'province', 'Centre', 'Salle', 'NumPlace', 'langues'
                ]].values.tolist()
                
                # Ajouter le mode de répartition à chaque ligne
                data = [list(row) + [mode_repartition] for row in data]
                
                # Insérer les nouvelles données
                cursor.executemany('''
                    INSERT INTO repartition 
                    (code, lastname, firstname, region, province, centre, salle, numplace, langues, mode_repartition)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Erreur lors de la sauvegarde de la répartition: {e}")
            return False
    
    def get_mode_repartition(self):
        """Récupère le mode de répartition actuel"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT mode_repartition
                    FROM repartition
                    ORDER BY date_repartition DESC
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                return result[0] if result else 'ALEATOIRE'
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération du mode de répartition: {e}")
            return 'ALEATOIRE'

    def get_last_repartition(self):
        """Récupère la dernière répartition sauvegardée"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        code as Code,
                        lastname as LastName,
                        firstname as FirstName,
                        region,
                        province,
                        centre as Centre,
                        salle as Salle,
                        numplace as NumPlace,
                        langues,
                        mode_repartition
                    FROM repartition
                    ORDER BY date_repartition DESC
                '''
                df = pd.read_sql_query(query, conn)
                return df if not df.empty else None
                
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération de la répartition: {e}")
            return None
