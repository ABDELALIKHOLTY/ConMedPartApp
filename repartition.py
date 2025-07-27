from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import Qt

from database.candidats_db import CandidatsDB
from database.salles_db import SallesDB
from database.repartition_db import RepartitionDB
import os
from datetime import datetime
import pandas as pd
import random
from reportlab import *
import sys
def lancer_repartition(self):
    """Lance la répartition des candidats dans les salles"""
    try:
        # Vérifier si les données sont disponibles
        if self.df_candidats is None or self.df_candidats.empty:
            self.afficher_message_erreur("Erreur", "Veuillez d'abord importer la liste des candidats.")
            return
            
        if self.df_salles is None or self.df_salles.empty:
            self.afficher_message_erreur("Erreur", "Veuillez d'abord configurer les salles.")
            return

        # Vérifier les colonnes requises pour les candidats
        candidats_cols_requises = ['Code', 'LastName', 'FirstName', 'region', 'province', 'langues']
        for col in candidats_cols_requises:
            if col not in self.df_candidats.columns:
                self.afficher_message_erreur("Erreur", f"Colonne manquante dans les candidats: {col}")
                return

        # Vérifier les colonnes requises pour les salles
        salles_cols_requises = ['centre', 'nom', 'capacite', 'type']
        for col in salles_cols_requises:
            if col not in self.df_salles.columns:
                self.afficher_message_erreur("Erreur", f"Colonne manquante dans les salles: {col}")
                return

        # Vérifier la capacité totale
        capacite_totale = self.df_salles['capacite'].sum()
        nb_candidats = len(self.df_candidats)
        
        if capacite_totale < nb_candidats:
            self.afficher_message_erreur("Erreur", 
                f"Capacité insuffisante: {capacite_totale} places pour {nb_candidats} candidats")
            return

        # Mettre à jour le statut
        self.card_status.update_value("En cours...")
        QApplication.processEvents()  # Pour mettre à jour l'interface

        # Choisir le mode de répartition
        if self.mode_priorite.isChecked():
            resultats = repartition_par_priorite(self)
        else:
            resultats = repartition_aleatoire(self)

        if resultats is None or resultats.empty:
            self.afficher_message_erreur("Erreur", "La répartition n'a généré aucun résultat")
            return

        # Sauvegarder les résultats
        self.resultats_repartition = resultats
        
        # Afficher les résultats
        afficher_resultats_repartition(self)
        
        # Mettre à jour le statut
        self.card_status.update_value("Terminé ✅")
        self.btn_export.setEnabled(True)
        
        # Afficher un message de succès
        self.afficher_message_succes("Répartition terminée", 
            f"La répartition des {nb_candidats} candidats est terminée avec succès.")

    except Exception as e:
        self.card_status.update_value("Erreur ❌")
        self.afficher_message_erreur("Erreur de répartition", str(e))
        import traceback
        traceback.print_exc()

def repartition_par_priorite(app):
    """Répartition par priorité en utilisant le centre d'examen assigné"""
    try:
        # Copier les DataFrames pour ne pas modifier les originaux
        candidats = app.df_candidats.copy()
        salles = app.df_salles.copy()
        
        # Vérifier que la colonne centreExamen existe
        if 'centreExamen' not in candidats.columns:
            raise ValueError("La colonne 'centreExamen' est requise dans le fichier des candidats")
        
        # Initialiser les structures de données
        salles_par_centre = {}
        salles_occupation = {}
        
        # Organiser les salles par centre
        for _, salle in salles.iterrows():
            centre = salle['centre'].strip()
            # Initialiser les dictionnaires pour ce centre s'ils n'existent pas
            if centre not in salles_par_centre:
                salles_par_centre[centre] = {'Grandes': [], 'Petites': []}
                salles_occupation[centre] = {}

            # Classer la salle selon son type et l'ajouter aux structures
            type_salle = 'Grandes' if salle['type'].strip() == 'Grande' else 'Petites'
            salles_par_centre[centre][type_salle].append(salle)
            
            # Initialiser le suivi d'occupation pour cette salle
            salles_occupation[centre][salle['nom']] = {
                'capacite': salle['capacite'],
                'places_occupees': 0,
                'type': salle['type']
            }
            
        # Vérifier que chaque centre a au moins une salle
        centres_vides = [centre for centre, salles in salles_par_centre.items() 
                        if len(salles['Grandes']) + len(salles['Petites']) == 0]
        if centres_vides:
            raise ValueError(f"Les centres suivants n'ont pas de salles : {', '.join(centres_vides)}")
        
        # Créer le mapping des centres d'examen vers les centres de salles
        mapping_centres = {}
        centres_examen_uniques = candidats['centreExamen'].dropna().unique()
        
        for centre_exam in centres_examen_uniques:
            centre_exam_clean = centre_exam.strip().lower()
            centre_trouve = None
            
            # D'abord chercher une correspondance exacte
            for centre_salle in salles_par_centre.keys():
                if centre_exam_clean == centre_salle.strip().lower():
                    centre_trouve = centre_salle
                    mapping_centres[centre_exam] = centre_salle
                    break
            
            # Si pas trouvé, chercher une correspondance partielle
            if not centre_trouve:
                for centre_salle in salles_par_centre.keys():
                    if (centre_exam_clean in centre_salle.strip().lower() or
                        centre_salle.strip().lower() in centre_exam_clean):
                        centre_trouve = centre_salle
                        mapping_centres[centre_exam] = centre_salle
                        break
            
            if not centre_trouve:
                raise ValueError(f"Centre d'examen '{centre_exam}' non trouvé dans la liste des salles disponibles")
        
        # Trier les candidats dans l'ordre souhaité
        candidats = candidats.sort_values(['centreExamen', 'region', 'province', 'langues', 'LastName', 'FirstName'])
        
        # Initialiser le DataFrame des résultats
        resultats = pd.DataFrame(columns=[
            'Code', 'LastName', 'FirstName', 'region', 'province', 
            'Centre', 'Salle', 'NumPlace', 'TypeSalle'
        ])
        
        # Traiter les candidats par centre d'examen
        for centre_examen, groupe in candidats.groupby('centreExamen', dropna=False):
            if pd.isna(centre_examen):
                raise ValueError("Des candidats n'ont pas de centre d'examen assigné")
            # Obtenir le centre réel correspondant au centre d'examen
            centre_reel = mapping_centres.get(centre_examen)
            if not centre_reel:
                raise ValueError(f"Impossible de trouver le centre correspondant pour '{centre_examen}'")
                
            # Répartir les candidats de ce groupe dans le centre
            for _, candidat in groupe.iterrows():
                place_trouvee = False
                
                # Essayer d'abord les grandes salles, puis les petites si nécessaire
                for type_salle in ['Grandes', 'Petites']:
                    if place_trouvee:
                        break
                        
                    for salle in salles_par_centre[centre_reel][type_salle]:
                        occupation = salles_occupation[centre_reel][salle['nom']]
                        
                        if occupation['places_occupees'] < occupation['capacite']:
                            # Placer le candidat
                            num_place = occupation['places_occupees'] + 1
                            
                            # Ajouter aux résultats
                            resultats = pd.concat([resultats, pd.DataFrame([{
                                'Code': candidat['Code'],
                                'LastName': candidat['LastName'],
                                'FirstName': candidat['FirstName'],
                                'region': candidat['region'],
                                'province': candidat['province'],
                                'Centre': centre_reel,
                                'Salle': salle['nom'],
                                'NumPlace': num_place,
                                'TypeSalle': salle['type'],
                                'langues': candidat['langues']
                            }])], ignore_index=True)
                            
                            # Mettre à jour l'occupation
                            occupation['places_occupees'] += 1
                            place_trouvee = True
                            break
                
                if not place_trouvee:
                    raise ValueError(f"Plus de places disponibles dans le centre '{centre_reel}' pour le candidat {candidat['Code']}")
        
            # Vérifier qu'on a bien placé tous les candidats
        if len(resultats) != len(candidats):
            raise ValueError(f"Erreur: seulement {len(resultats)} candidats placés sur {len(candidats)}")
            
        return resultats
                            
                            # Ajouter aux résultats

        for (region, province), groupe in candidats.groupby(['region', 'province']):
            # Trouver le centre correspondant à la région/province
            centre_trouve = None
            
            # Si aucun centre n'est trouvé, prendre le premier centre disponible
            if centre_trouve is None and salles_par_centre:
                centre_trouve = list(salles_par_centre.keys())[0]
                print(f"Aucun centre trouvé pour {region}, utilisation du centre par défaut: {centre_trouve}")
            
            if centre_trouve is None:
                print(f"Erreur: Aucun centre disponible pour région: {region}, province: {province}")
                continue
                
            # D'abord essayer les grandes salles
            for candidat in groupe.itertuples():
                placee = False
                
                # Essayer d'abord les grandes salles
                for salle in salles_par_centre[centre_trouve]['Grandes']:
                    if salles_occupation[centre_trouve][salle['nom']]['places_occupees'] < salle['capacite']:
                        # Ajouter le candidat à cette salle
                        new_row = {
                            'Code': candidat.Code,
                            'LastName': candidat.LastName,
                            'FirstName': candidat.FirstName,
                            'region': candidat.region,
                            'province': candidat.province,
                            'Centre': centre_trouve,
                            'Salle': salle['nom'],
                            'NumPlace': salles_occupation[centre_trouve][salle['nom']]['places_occupees'] + 1,
                            'TypeSalle': salle['type']
                        }
                        resultats = pd.concat([resultats, pd.DataFrame([new_row])], ignore_index=True)
                        salles_occupation[centre_trouve][salle['nom']]['places_occupees'] += 1
                        placee = True
                        break
                        
                # Si pas placé dans une grande salle, essayer les petites salles
                if not placee:
                    for salle in salles_par_centre[centre_trouve]['Petites']:
                        if salles_occupation[centre_trouve][salle['nom']]['places_occupees'] < salle['capacite']:
                            # Ajouter le candidat à cette salle
                            new_row = {
                                'Code': candidat['Code'],
                                'LastName': candidat['LastName'],
                                'FirstName': candidat['FirstName'],
                                'region': candidat['region'],
                                'province': candidat['province'],
                                'Centre': centre_trouve,
                                'Salle': salle['nom'],
                                'NumPlace': salles_occupation[centre_trouve][salle['nom']]['places_occupees'] + 1,
                                'TypeSalle': salle['type']
                            }
                            resultats = pd.concat([resultats, pd.DataFrame([new_row])], ignore_index=True)
                            salles_occupation[centre_trouve][salle['nom']]['places_occupees'] += 1
                            placee = True
                            break
            
            if not placee:
                raise Exception(f"Impossible de placer le candidat {candidat['Code']} - Plus de places disponibles")
        
        return resultats
        
    except Exception as e:
        app.afficher_message_erreur("Erreur", f"Erreur lors de la répartition par priorité : {str(e)}")
        return None

def repartition_aleatoire(app):
    """Répartition aléatoire en respectant les centres d'examen assignés"""
    try:
        # Copier les DataFrames pour ne pas modifier les originaux
        candidats = app.df_candidats.copy()
        salles = app.df_salles.copy()
        
        # Vérifier que la colonne centreExamen existe
        if 'centreExamen' not in candidats.columns:
            raise ValueError("La colonne 'centreExamen' est requise dans le fichier des candidats")
        
        # Initialiser les structures de données
        salles_par_centre = {}
        salles_occupation = {}
        
        # Organiser les salles par centre
        for _, salle in salles.iterrows():
            centre = salle['centre'].strip()
            if centre not in salles_par_centre:
                salles_par_centre[centre] = {'Grandes': [], 'Petites': []}
                salles_occupation[centre] = {}
            
            # Classer la salle selon son type
            type_salle = 'Grandes' if salle['type'].strip() == 'Grande' else 'Petites'
            salles_par_centre[centre][type_salle].append(salle)
            
            # Initialiser l'occupation
            salles_occupation[centre][salle['nom']] = {
                'capacite': salle['capacite'],
                'places_occupees': 0,
                'type': salle['type']
            }
        
        # Créer le mapping des centres d'examen vers les centres de salles
        mapping_centres = {}
        centres_examen_uniques = candidats['centreExamen'].dropna().unique()
        
        # Créer les correspondances entre centres d'examen et centres réels
        for centre_exam in centres_examen_uniques:
            centre_exam_clean = centre_exam.strip().lower()
            centre_trouve = None
            
            # D'abord chercher une correspondance exacte
            for centre_salle in salles_par_centre.keys():
                if centre_exam_clean == centre_salle.strip().lower():
                    centre_trouve = centre_salle
                    mapping_centres[centre_exam] = centre_salle
                    break
            
            # Si pas trouvé, chercher une correspondance partielle
            if not centre_trouve:
                for centre_salle in salles_par_centre.keys():
                    if (centre_exam_clean in centre_salle.strip().lower() or
                        centre_salle.strip().lower() in centre_exam_clean):
                        centre_trouve = centre_salle
                        mapping_centres[centre_exam] = centre_salle
                        break
            
            if not centre_trouve:
                raise ValueError(f"Centre d'examen '{centre_exam}' non trouvé dans la liste des salles disponibles")

        # Initialiser le DataFrame des résultats
        resultats = pd.DataFrame(columns=[
            'Code', 'LastName', 'FirstName', 'region', 'province', 
            'Centre', 'Salle', 'NumPlace', 'TypeSalle'
        ])
        
        # Mélanger aléatoirement les candidats tout en respectant region/province/langues et centre
        candidats_groupes = []
        for centre_examen in centres_examen_uniques:
            # Pour chaque centre, grouper par région, province et langues
            centre_groupe = candidats[candidats['centreExamen'] == centre_examen]
            for (region, province, langues), sous_groupe in centre_groupe.groupby(['region', 'province', 'langues']):
                # Mélanger aléatoirement chaque sous-groupe
                sous_groupe = sous_groupe.copy()
                sous_groupe = sous_groupe.sample(frac=1).reset_index(drop=True)
                candidats_groupes.append(sous_groupe)
        
        # Reconstituer le DataFrame avec tous les groupes mélangés
        candidats = pd.concat(candidats_groupes, ignore_index=True)
        
        # Traiter les candidats par centre d'examen
        for centre_examen, groupe in candidats.groupby('centreExamen', dropna=False):
            if pd.isna(centre_examen):
                raise ValueError("Des candidats n'ont pas de centre d'examen assigné")
            
            # Obtenir le centre réel correspondant au centre d'examen
            centre_reel = mapping_centres.get(centre_examen)
            if not centre_reel:
                raise ValueError(f"Impossible de trouver le centre correspondant pour '{centre_examen}'")
            
            # Répartir les candidats de ce groupe dans le centre
            for _, candidat in groupe.iterrows():
                placee = False
                
                # Essayer d'abord les grandes salles
                for salle in salles_par_centre[centre_reel]['Grandes']:
                    if salles_occupation[centre_reel][salle['nom']]['places_occupees'] < salle['capacite']:
                        new_row = {
                            'Code': candidat['Code'],
                            'LastName': candidat['LastName'],
                            'FirstName': candidat['FirstName'],
                            'region': candidat['region'],
                            'province': candidat['province'],
                            'Centre': centre_reel,
                            'Salle': salle['nom'],
                            'NumPlace': salles_occupation[centre_reel][salle['nom']]['places_occupees'] + 1,
                            'TypeSalle': salle['type'],
                            'langues': candidat['langues']
                        }
                        resultats = pd.concat([resultats, pd.DataFrame([new_row])], ignore_index=True)
                        salles_occupation[centre_reel][salle['nom']]['places_occupees'] += 1
                        placee = True
                        break
                        
                # Si pas placé dans une grande salle, essayer les petites salles
                if not placee:
                    for salle in salles_par_centre[centre_reel]['Petites']:
                        if salles_occupation[centre_reel][salle['nom']]['places_occupees'] < salle['capacite']:
                            new_row = {
                                'Code': candidat['Code'],
                                'LastName': candidat['LastName'],
                                'FirstName': candidat['FirstName'],
                                'region': candidat['region'],
                                'province': candidat['province'],
                                'Centre': centre_reel,
                                'Salle': salle['nom'],
                                'NumPlace': salles_occupation[centre_reel][salle['nom']]['places_occupees'] + 1,
                                'TypeSalle': salle['type'],
                                'langues': candidat['langues']
                            }
                            resultats = pd.concat([resultats, pd.DataFrame([new_row])], ignore_index=True)
                            salles_occupation[centre_reel][salle['nom']]['places_occupees'] += 1
                            placee = True
                            break
            
                if not placee:
                    raise Exception(f"Impossible de placer le candidat {candidat['Code']} - Plus de places disponibles dans le centre {centre_reel}")
        
        # Vérifier que tous les candidats ont été placés
        if len(resultats) != len(candidats):
            raise Exception(f"Certains candidats n'ont pas pu être placés. {len(candidats) - len(resultats)} candidats non placés.")
        
        return resultats
        
    except Exception as e:
        app.afficher_message_erreur("Erreur", f"Erreur lors de la répartition aléatoire : {str(e)}")
        return None

def afficher_resultats_repartition(app):
    """Affiche les résultats de la répartition dans le tableau et sauvegarde dans la base de données"""
    try:
        if app.resultats_repartition is None or app.resultats_repartition.empty:
            raise Exception("Aucun résultat à afficher")
            
        # Sauvegarder les résultats dans la base de données
        db = RepartitionDB()
        if not db.save_repartition(app.resultats_repartition):
            app.afficher_message_erreur("Erreur", "Impossible de sauvegarder la répartition dans la base de données")
            
        # Configurer le tableau
        app.results_table.clearSpans()
        app.results_text.setVisible(False)
        app.results_table.setVisible(True)
        app.results_table.clear()
        
        # Définir les colonnes à afficher
        colonnes_a_afficher = [
            'Code', 'LastName', 'FirstName', 'region', 'province',
            'Centre', 'Salle', 'NumPlace', 'langues'
        ]
        
        app.results_table.setRowCount(len(app.resultats_repartition))
        app.results_table.setColumnCount(len(colonnes_a_afficher))
        app.results_table.setHorizontalHeaderLabels(colonnes_a_afficher)
        
        # Remplir le tableau
        for i, (_, row) in enumerate(app.resultats_repartition.iterrows()):
            for j, col in enumerate(colonnes_a_afficher):
                item = QTableWidgetItem(str(row[col]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Mettre en rouge les petites salles
                if col == 'TypeSalle' and row[col] == 'Petite':
                    item.setForeground(QBrush(QColor("#FF0000")))
                
                app.results_table.setItem(i, j, item)
        
        # Ajuster la taille des colonnes
        app.results_table.resizeColumnsToContents()
        
        # Définir une hauteur fixe pour les lignes
        for i in range(app.results_table.rowCount()):
            app.results_table.setRowHeight(i, 30)
            
    except Exception as e:
        app.results_table.setVisible(False)
        app.results_text.setVisible(True)
        app.results_text.setText(f"Erreur lors de l'affichage: {str(e)}")

def exporter_resultats(self):
    """Exporte les résultats de la répartition vers un fichier Excel"""
    try:
        if self.resultats_repartition is None or self.resultats_repartition.empty:
            self.afficher_message_erreur("Erreur", "Aucun résultat à exporter")
            return
            
        # Demander où sauvegarder le fichier
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer les résultats", 
            "repartition_candidats.xlsx", 
            "Fichiers Excel (*.xlsx)"
        )
        
        if not file_path:
            return  # L'utilisateur a annulé
            
        # Créer un DataFrame avec les résultats
        df_resultats = self.resultats_repartition.copy()
        
        # Ajouter des statistiques par centre
        stats_centres = df_resultats.groupby('Centre').agg({
            'Code': 'count',
            'TypeSalle': lambda x: (x == 'Grande').sum()
        }).rename(columns={
            'Code': 'Nombre de candidats',
            'TypeSalle': 'Nombre de grandes salles utilisées'
        }).reset_index()
        
        # Sauvegarder dans un fichier Excel avec plusieurs onglets
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_resultats.to_excel(writer, sheet_name='Répartition détaillée', index=False)
            stats_centres.to_excel(writer, sheet_name='Statistiques par centre', index=False)
            
            # Ajouter un onglet avec les salles non utilisées
            salles_utilisees = df_resultats[['Centre', 'Salle']].drop_duplicates()
            salles_totales = self.df_salles[['centre', 'nom']].rename(columns={'centre': 'Centre', 'nom': 'Salle'})
            salles_non_utilisees = salles_totales.merge(
                salles_utilisees, on=['Centre', 'Salle'], how='left', indicator=True
            ).query('_merge == "left_only"').drop('_merge', axis=1)
            
            salles_non_utilisees.to_excel(writer, sheet_name='Salles non utilisées', index=False)
        
        self.afficher_message_succes("Export réussi", 
            f"Les résultats ont été exportés avec succès dans:\n{file_path}")
            
    except Exception as e:
        self.afficher_message_erreur("Erreur d'export", f"Erreur lors de l'export: {str(e)}")