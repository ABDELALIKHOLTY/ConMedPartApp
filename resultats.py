from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import Qt
from widgets import ModernButton
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from database.candidats_db import CandidatsDB
from database.salles_db import SallesDB
from database.repartition_db import RepartitionDB

def get_current_room(page_content):
    """Helper pour extraire le numéro de salle de la page courante."""
    if "SALLE :" in page_content:
        import re
        match = re.search(r"SALLE : (\S+)", page_content)
        if match:
            return match.group(1)
    return None

class ResultatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Résultats")
        self.setMinimumWidth(800)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.1);
            }
        """)
        self.setup_ui()
        # Charger les centres immédiatement après l'initialisation de l'interface
        self.charger_centres()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("<span style='color:#3498db; font-size:22px; font-weight:bold; font-family:Arial;'>Gestion des Résultats</span>")
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Container principal
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: rgba(50, 50, 60, 0.7);
                border-radius: 5px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QComboBox {
                background-color: rgba(60, 60, 70, 0.7);
                color: white;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 5px;
                padding: 5px;
                min-width: 200px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(20)

        # Section sélection du centre
        selection_group = QGroupBox("Sélection du Centre")
        selection_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        selection_layout = QVBoxLayout(selection_group)
        
        self.centres_combo = QComboBox()
        self.centres_combo.addItem("Tous les centres")
        selection_layout.addWidget(self.centres_combo)
        
        main_layout.addWidget(selection_group)

        # Section boutons
        buttons_group = QGroupBox("Documents à Générer")
        buttons_group.setStyleSheet(selection_group.styleSheet())
        buttons_layout = QVBoxLayout(buttons_group)
        
        self.btn_affichage = QPushButton("Feuilles d'affichage")
        self.btn_presence = QPushButton("Feuilles de Présence")
        self.btn_all = QPushButton("Tous les Documents")
        self.btn_all.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        buttons_layout.addWidget(self.btn_affichage)
        buttons_layout.addWidget(self.btn_presence)
        buttons_layout.addWidget(self.btn_all)

        main_layout.addWidget(buttons_group)
        layout.addWidget(main_container)

        # Boutons de contrôle
        buttons_container = QFrame()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addWidget(buttons_container)
        
        # Connecter les signaux
        self.btn_affichage.clicked.connect(self.generer_affichage)
        self.btn_presence.clicked.connect(self.generer_presence)
        self.btn_all.clicked.connect(self.generer_tous_documents)
        
    def charger_centres(self):
        try:
            # Récupérer la dernière répartition
            repartition_db = RepartitionDB()
            derniere_repartition = repartition_db.get_last_repartition()
            
            if derniere_repartition is None or derniere_repartition.empty:
                QMessageBox.warning(self, "Attention", "Aucune répartition trouvée")
                return
                
            # Récupérer les centres uniques de la dernière répartition
            centres_utilises = sorted(derniere_repartition['Centre'].unique())
            
            # Mettre à jour la combobox
            self.centres_combo.clear()
            self.centres_combo.addItem("Tous les centres")
            
            for centre in centres_utilises:
                if centre and not pd.isna(centre):  # Vérifier que le centre n'est pas vide ou NaN
                    self.centres_combo.addItem(str(centre))
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des centres: {str(e)}")
            
    def generer_affichage(self):
        try:
            centre_selected = self.centres_combo.currentText()
            if centre_selected == "Tous les centres":
                self.generer_affichage_tous_centres()
            else:
                self.generer_affichage_centre(centre_selected)
            QMessageBox.information(self, "Succès", "Les fichiers d'affichage ont été générés avec succès!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération des fichiers d'affichage: {str(e)}")
            
    def generer_presence(self):
        try:
            centre_selected = self.centres_combo.currentText()
            if centre_selected == "Tous les centres":
                self.generer_presence_tous_centres()
            else:
                self.generer_presence_centre(centre_selected)
            QMessageBox.information(self, "Succès", "Les feuilles de présence ont été générées avec succès!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération des feuilles de présence: {str(e)}")

    def generer_presence_tous_centres(self):
        try:
            centres = [self.centres_combo.itemText(i) for i in range(1, self.centres_combo.count())]
            for centre in centres:
                self.generer_presence_centre(centre)
        except Exception as e:
            raise Exception(f"Erreur lors de la génération pour tous les centres: {str(e)}")

    def generer_presence_centre(self, centre):
        try:
            # Récupérer la dernière répartition pour ce centre
            repartition_db = RepartitionDB()
            candidats_db = CandidatsDB()
            
            derniere_repartition = repartition_db.get_last_repartition()
            if derniere_repartition is None:
                raise Exception("Aucune répartition trouvée")
                
            # Filtrer pour le centre sélectionné et convertir en dictionnaire pour un accès plus facile
            resultats_centre = derniere_repartition[derniere_repartition['Centre'].astype(str) == str(centre)]
            if len(resultats_centre) == 0:
                raise Exception(f"Aucun candidat trouvé pour le centre {centre}")
            
            # Demander l'emplacement de sauvegarde
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer la feuille de présence",
                f"Feuille_Presence_{str(centre).replace(' ', '_')}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            
            if not filename:
                return  # L'utilisateur a annulé
                
            # Créer le document PDF avec des marges réduites
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                topMargin=3,
                bottomMargin=55,
                leftMargin=15,
                rightMargin=15
            )
            
            elements = []
            
            # Configuration de la page
            styles = getSampleStyleSheet()
            
            # Ajouter le logo avec dimensions optimisées
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Logopdf.jpg")
            
            # Styles des titres
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading2'],
                fontSize=14,
                alignment=1,
                spaceAfter=5,
                spaceBefore=5
            )          
            
            # Pour chaque salle, créer un tableau des candidats
            headers = ['CNE', 'NOM', 'PRÉNOM', 'PLACE', 'PRÉSENCE']
            
            # Style pour les en-têtes de salle
            salle_style = ParagraphStyle(
                'SalleStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=5,
                spaceBefore=5,
                textColor=colors.HexColor('#000000')
            )
            
            # Style du tableau
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            # Préparer les données par salle
            salles = sorted(resultats_centre['Salle'].unique(), key=str)
            resultats_par_salle = {}
            
            # Pré-traiter les données pour chaque salle
            for salle in salles:
                mask = resultats_centre['Salle'].astype(str) == str(salle)
                resultats_par_salle[str(salle)] = resultats_centre[mask].copy()
            
            # Garder l'ordre original des candidats et grouper par salle
            for idx, salle in enumerate(salles):
                salle_str = str(salle)
                candidats_salle = resultats_par_salle[salle_str]
                
                # Ajouter le logo et les titres pour chaque nouvelle salle
                if os.path.exists(logo_path):
                    try:
                        img = Image(logo_path, width=550, height=60)
                        img.hAlign = 'CENTER'
                        elements.append(img)
                     
                    except Exception as e:
                        print(f"Erreur lors du chargement du logo: {str(e)}")

                # Ajouter les titres pour chaque salle
                elements.append(Paragraph("CANDIDATS PRÉSÉLECTIONNÉS POUR PASSER LE CONCOURS D'ACCÈS", title_style))
                elements.append(Paragraph("AUX ÉTUDES MÉDICALES, PHARMACEUTIQUES", title_style))
                # En-tête pour chaque salle
                elements.append(Paragraph(f"CENTRE D'EXAMEN : {centre}", salle_style))
                elements.append(Paragraph(f"SALLE : {salle_str}", salle_style))
                
                # Créer une nouvelle liste de données pour cette salle
                data = [headers]
                
                # Traiter les candidats de la salle
                candidats_data = []
                for _, row in candidats_salle.iterrows():
                    try:
                        code = str(row['Code']) if pd.notna(row['Code']) else "N/A"
                        nom = str(row['LastName']) if pd.notna(row['LastName']) else "N/A"
                        prenom = str(row['FirstName']) if pd.notna(row['FirstName']) else "N/A"
                        num_place = str(row['NumPlace']) if pd.notna(row['NumPlace']) else "N/A"
                        
                        candidats_data.append([
                            code,
                            nom,
                            prenom,
                            num_place,
                            ''  # Colonne vide pour la présence
                        ])
                    except Exception as e:
                        print(f"Erreur lors du traitement du candidat: {str(e)}")
                        continue
                
                # Ajouter les données au tableau
                data.extend(candidats_data)
                
                # Créer et ajouter le tableau pour cette salle avec des largeurs de colonnes optimisées
                col_widths = [
                    doc.width * 0.2,
                    doc.width * 0.25,
                    doc.width * 0.25,
                    doc.width * 0.15,
                    doc.width * 0.15
                ]
                table = Table(data, colWidths=col_widths, repeatRows=1)
                table.setStyle(table_style)
                elements.append(table)
                
                if idx < len(salles) - 1:  # Ne pas ajouter de saut de page après la dernière salle
                    elements.append(PageBreak())
            
            # Ajouter le pied de page
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=1,
                bottomMargin=20
            )
            
            footer_text = """
            <para align=center>
            Faculté de Médecine et de Pharmacie de Fès BP,1893; Km 2.200 Route Sidi Harazem<br/>
            Tél : 0535619318 | Fax : 0535619321 |  Web : www.fmp-usmba.ac.ma | E-Mail : contact@fmpf-usmba.ac.ma
            </para>
            """
            
            # Variables pour suivre la pagination par salle
            current_room = None
            page_counter = 1
            
            def add_page_number(canvas, doc):
                canvas.saveState()
                nonlocal current_room, page_counter
                
                # Vérifier si on est sur une nouvelle salle
                current_text = ' '.join(str(item) for item in canvas._code if isinstance(item, str))
                if "SALLE :" in current_text:
                    import re
                    match = re.search(r"SALLE : (\S+)", current_text)
                    if match and match.group(1) != current_room:
                        current_room = match.group(1)
                        page_counter = 1
                
                # Ajouter le pied de page
                canvas.setFont('Helvetica', 9)
                footer = footer_text.replace('<para align=center>', '').replace('</para>', '').strip()
                y_position = 45
                page_width = doc.pagesize[0]
                
                for line in footer.split('<br/>'):
                    line = line.strip()
                    text_width = canvas.stringWidth(line, 'Helvetica', 9)
                    x_position = (page_width - text_width) / 2
                    canvas.drawString(x_position, y_position, line)
                    y_position -= 12
                
                # Ajouter le numéro de page
                canvas.setFont('Helvetica', 9)
                page_number_text = f"Page {page_counter}"
                text_width = canvas.stringWidth(page_number_text, 'Helvetica', 9)
                x_position = (page_width - text_width) / 2
                canvas.drawString(x_position, 15, page_number_text)
                
                page_counter += 1
                canvas.restoreState()
            
            # Générer le PDF avec numérotation des pages
            doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération pour le centre {centre}: {str(e)}")
            
    def generer_tous_documents(self):
        try:
            self.generer_affichage()
            self.generer_presence()
            QMessageBox.information(self, "Succès", "Tous les documents ont été générés avec succès!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération de tous les documents: {str(e)}")
            
    def generer_affichage_tous_centres(self):
        try:
            # Get centers from combo box
            centres = [self.centres_combo.itemText(i) for i in range(1, self.centres_combo.count())]
            
            # Generate PDF for each center
            for centre in centres:
                self.generer_affichage_centre(centre)
                
        except Exception as e:
            raise Exception(f"Erreur lors de la génération pour tous les centres: {str(e)}")
            
    def generer_affichage_centre(self, centre):
        try:
            # Récupérer la dernière répartition pour ce centre
            repartition_db = RepartitionDB()
            candidats_db = CandidatsDB()
            
            derniere_repartition = repartition_db.get_last_repartition()
            if derniere_repartition is None:
                raise Exception("Aucune répartition trouvée")
                
            # Filtrer pour le centre sélectionné et convertir en dictionnaire pour un accès plus facile
            resultats_centre = derniere_repartition[derniere_repartition['Centre'].astype(str) == str(centre)]
            if len(resultats_centre) == 0:
                raise Exception(f"Aucun candidat trouvé pour le centre {centre}")
            
            # Demander l'emplacement de sauvegarde
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer le fichier d'affichage",
                f"Affichage_{str(centre).replace(' ', '_')}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            
            if not filename:
                return  # L'utilisateur a annulé
                
            # Créer le document PDF avec des marges réduites
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                topMargin=3,
                bottomMargin=55,
                leftMargin=15,
                rightMargin=15
            )
            
            elements = []
            
            # Configuration de la page
            styles = getSampleStyleSheet()
            
            # Ajouter le logo avec dimensions optimisées
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Logopdf.jpg")
            
            
            # Styles des titres
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading2'],
                fontSize=14,
                alignment=1, 
                spaceAfter=5,
                spaceBefore=5
            )          
            
           
            # Pour chaque salle, créer un tableau des candidats
            headers = ['CNE', 'NOM', 'PRÉNOM', 'LIEU D\'EXAMEN', 'PLACE']
            
            # Style pour les en-têtes de salle
            salle_style = ParagraphStyle(
                'SalleStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=5,
                spaceBefore=5,
                textColor=colors.HexColor('#000000')
            )
            
            # Style du tableau
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 11),  # Taille de police pour le contenu
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),  # Padding supérieur pour toutes les cellules
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),  # Padding inférieur pour le contenu
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),  # Padding droit
                ('LEFTPADDING', (0, 0), (-1, -1), 10),  # Padding gauche
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            # Dictionnaire pour stocker les compteurs de page par salle
            page_counters = {}
            
            def add_page_number(canvas, doc):
                canvas.saveState()
                
                # Identifier la salle actuelle
                current_page_content = ' '.join([str(item) for item in canvas._code if isinstance(item, str)])
                current_salle = None
                
                # Chercher le numéro de salle dans le contenu de la page
                if "SALLE :" in current_page_content:
                    import re
                    match = re.search(r"SALLE : (.+?)(?=\n|$)", current_page_content)
                    if match:
                        current_salle = match.group(1).strip()
                
                # Initialiser ou incrémenter le compteur pour cette salle
                if current_salle:
                    if current_salle not in page_counters:
                        page_counters[current_salle] = 1
                    current_page = page_counters[current_salle]
                    page_counters[current_salle] += 1
                else:
                    current_page = canvas.getPageNumber()
                
                # Ajouter le pied de page
                canvas.setFont('Helvetica', 9)
                footer = footer_text.replace('<para align=center>', '').replace('</para>', '').strip()
                y_position = 45
                page_width = doc.pagesize[0]
                
                for line in footer.split('<br/>'):
                    line = line.strip()
                    text_width = canvas.stringWidth(line, 'Helvetica', 9)
                    x_position = (page_width - text_width) / 2
                    canvas.drawString(x_position, y_position, line)
                    y_position -= 12
                
                # Ajouter le numéro de page qui recommence à 1 pour chaque salle
                canvas.setFont('Helvetica', 9)
                page_number_text = f"Page {current_page}"
                text_width = canvas.stringWidth(page_number_text, 'Helvetica', 9)
                x_position = (page_width - text_width) / 2
                canvas.drawString(x_position, 15, page_number_text)
                canvas.restoreState()
            
            # Préparer les données par salle de manière plus robuste
            salles = sorted(resultats_centre['Salle'].unique(), key=str)
            resultats_par_salle = {}
            
            # Pré-traiter les données pour chaque salle
            for salle in salles:
                mask = resultats_centre['Salle'].astype(str) == str(salle)
                resultats_par_salle[str(salle)] = resultats_centre[mask].copy()
            
            # Garder l'ordre original des candidats et grouper par salle
            for idx, salle in enumerate(salles):
                salle_str = str(salle)
                candidats_salle = resultats_par_salle[salle_str]
                
                # Ajouter le logo et les titres pour chaque nouvelle salle
                if os.path.exists(logo_path):
                    try:
                        img = Image(logo_path, width=550, height=60)
                        img.hAlign = 'CENTER'
                        elements.append(img)
                     
                    except Exception as e:
                        print(f"Erreur lors du chargement du logo: {str(e)}")

                # Ajouter les titres pour chaque salle
                elements.append(Paragraph("CANDIDATS PRÉSÉLECTIONNÉS POUR PASSER LE CONCOURS D'ACCÈS", title_style))
                elements.append(Paragraph("AUX ÉTUDES MÉDICALES, PHARMACEUTIQUES", title_style))
                # En-tête pour chaque salle
                elements.append(Paragraph(f"CENTRE D'EXAMEN : {centre}", salle_style))
                elements.append(Paragraph(f"SALLE : {salle_str}", salle_style))
                
                # Créer une nouvelle liste de données pour cette salle
                data = [headers]
                
                # Traiter les candidats de la salle de manière plus sûre
                candidats_data = []
                for _, row in candidats_salle.iterrows():
                    try:
                        code = str(row['Code']) if pd.notna(row['Code']) else "N/A"
                        nom = str(row['LastName']) if pd.notna(row['LastName']) else "N/A"
                        prenom = str(row['FirstName']) if pd.notna(row['FirstName']) else "N/A"
                        num_place = str(row['NumPlace']) if pd.notna(row['NumPlace']) else "N/A"
                        
                        candidats_data.append([
                            code,
                            nom,
                            prenom,
                            str(salle),
                            num_place
                        ])
                    except Exception as e:
                        print(f"Erreur lors du traitement du candidat {code}: {str(e)}")
                        continue
                
                # Ajouter les données au tableau
                data.extend(candidats_data)
                
                # Créer et ajouter le tableau pour cette salle avec des largeurs de colonnes optimisées
                # Ajuster les largeurs des colonnes pour mieux gérer le texte arabe
                col_widths = [
                    doc.width * 0.2,  # CNE
                    doc.width * 0.25,  # NOM (plus large pour l'arabe)
                    doc.width * 0.25,  # PRENOM (plus large pour l'arabe)
                    doc.width * 0.2,   # LIEU D'EXAMEN
                    doc.width * 0.1    # PLACE
                ]
                table = Table(data, colWidths=col_widths, repeatRows=1)
                table.setStyle(table_style)
                elements.append(table)
                
                # Ajouter un saut de page après chaque salle (sauf la dernière)
                if idx < len(salles) - 1:
                    elements.append(PageBreak())
            
            # Style du tableau est déjà défini dans le code précédent
            
            # Ajouter le pied de page
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=1,
               bottomMargin=20
            )
            
            footer_text = """
            <para align=center>
            Faculté de Médecine et de Pharmacie de Fès BP,1893; Km 2.200 Route Sidi Harazem<br/>
            Tél : 0535619318 | Fax : 0535619321 |  Web : www.fmp-usmba.ac.ma | E-Mail : contact@fmpf-usmba.ac.ma
            </para>
            """
            
            # Variables pour suivre la pagination par salle
            current_room = None
            page_counter = 1
            
            def add_page_number(canvas, doc):
                canvas.saveState()
                nonlocal current_room, page_counter
                
                # Détecter changement de salle en vérifiant le contenu du canvas
                current_page_content = canvas._code
                new_room = None
                for item in current_page_content:
                    if isinstance(item, str) and "SALLE :" in item:
                        new_room = item
                        break
                
                # Réinitialiser le compteur si on change de salle
                if new_room != current_room:
                    current_room = new_room
                    page_counter = 1
                
                # Ajouter le pied de page
                canvas.setFont('Helvetica', 9)
                footer = footer_text.replace('<para align=center>', '').replace('</para>', '').strip()
                y_position = 45
                page_width = doc.pagesize[0]
                
                for line in footer.split('<br/>'):
                    line = line.strip()
                    text_width = canvas.stringWidth(line, 'Helvetica', 9)
                    x_position = (page_width - text_width) / 2
                    canvas.drawString(x_position, y_position, line)
                    y_position -= 12
                
                # Ajouter le numéro de page qui recommence à 1 pour chaque salle
                canvas.setFont('Helvetica', 9)
                page_number_text = f"Page {page_counter}"
                text_width = canvas.stringWidth(page_number_text, 'Helvetica', 9)
                x_position = (page_width - text_width) / 2
                canvas.drawString(x_position, 15, page_number_text)
                
                page_counter += 1
                canvas.restoreState()
            
            # Générer le PDF avec numérotation des pages
            doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération pour le centre {centre}: {str(e)}")
    
    def add_room_table(self, elements, data):
        # Create table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Create table
        table = Table(data)
        table.setStyle(style)
        elements.append(table)


