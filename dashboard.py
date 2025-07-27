from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import Qt
from widgets import *
from salles import *
from database.candidats_db import CandidatsDB
from database.salles_db import SallesDB
import os
from datetime import datetime
import pandas as pd
import random
from reportlab import *
import sys
from PyQt6.QtWidgets import QApplication
from repartition import *
from resultats import ResultatsDialog

class ConMedPartApp(QMainWindow):
    def __init__(self):
        """Initialise l'application principale"""
        super().__init__()
        self.setWindowTitle("ConMedPartApp")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Initialisation des bases de données et chargement des données
        try:
            self.candidats_db = CandidatsDB()
            self.salles_db = SallesDB()
            
            # Créer au moins un centre par défaut si nécessaire
            self.salles_db.add_centre_if_empty("Centre par défaut")
            
        except Exception as e:
            print(f"Erreur d'initialisation des bases de données: {e}")
            
        # Variables d'état
        self.fichier_candidats = None
        self.fichier_salles = None
        self.nb_candidats = 0
        self.nb_salles = 0
        self.resultats_repartition = None
        
        # DataFrames (initialisés comme vides pour éviter les None)
        self.df_candidats = pd.DataFrame()
        self.df_salles = pd.DataFrame()
        
        # Configuration de la mémoire pour pandas
        pd.options.mode.chained_assignment = None
        
        self.setup_ui()
        self.apply_dark_theme()
        
        # Configurer le garbage collector pour une meilleure gestion de la mémoire
        import gc
        gc.enable()

    def setup_ui(self):
        # Widget principal avec fond
        self.background_widget = BackgroundWidget()
        self.setCentralWidget(self.background_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        self.create_header(main_layout)
        
        # Contenu principal
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Sidebar
        self.create_sidebar(content_layout)
        
        # Zone principale
        self.create_main_content(content_layout)
        
        main_layout.addLayout(content_layout)
        self.background_widget.setLayout(main_layout)
        
        # Charger les données des bases de données
        self.charger_donnees_db()
        self.mettre_a_jour_stats()

    def create_header(self, layout):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Header title
        title = QLabel("ConMedPartApp")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #3498db;  ")

        subtitle = QLabel("Répartition Automatisée des Candidats aux Concours Médicaux")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #aaaaaa; background: transparent;")

        # Logo image (match header height)
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "Logofmpf.png")
        if os.path.exists(logo_path):
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(logo_path)
          
            pixmap = pixmap.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setFixedHeight(60)
            logo_label.setStyleSheet("background: transparent;")
        else:
            logo_label.setText("")
            logo_label.setFixedHeight(60)
            logo_label.setStyleSheet("background: transparent;")

        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        header.setLayout(header_layout)
        layout.addWidget(header)

    def create_sidebar(self, layout):
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(15)
        
        # Section Import
        import_section = QFrame()
        import_section.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        import_layout = QVBoxLayout()
        import_layout.setSpacing(10)
        
        import_title = QLabel("Importer Fichiers")
        import_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        import_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        import_title.setStyleSheet("color: white; font-weight: bold;")
        
        self.btn_import_candidats = ModernButton("Importer Liste Candidats")
        self.btn_import_candidats.clicked.connect(lambda: self.import_file('candidats'))
        
        self.btn_import_salles = ModernButton("Gestion des Salles")
        self.btn_import_salles.clicked.connect(lambda: self.import_file('salles'))
        
        self.info_candidats = QLabel("Aucun fichier sélectionné")
        self.info_candidats.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        
        self.info_salles = QLabel("Aucun fichier sélectionné")
        self.info_salles.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        
        import_layout.addWidget(import_title)
        import_layout.addWidget(self.btn_import_candidats)
        import_layout.addWidget(self.info_candidats)
        import_layout.addWidget(self.btn_import_salles)
        import_layout.addWidget(self.info_salles)
        import_section.setLayout(import_layout)
        
        # Section Configuration
        config_section = QFrame()
        config_section.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        config_layout = QVBoxLayout()
        config_layout.setSpacing(10)
        
        config_title = QLabel("Configuration")
        config_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        config_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        config_title.setStyleSheet("color: white; ")
        
        priority_label = QLabel("Mode de répartition :")
        priority_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        priority_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        priority_label.setStyleSheet("color: white; ")
        
        # Radio buttons pour le choix du mode
        self.mode_group = QButtonGroup(self)
        
        self.mode_priorite = QRadioButton("Priorité: Rég/prov/OrAlphabétique")
        self.mode_priorite.setChecked(True)
        self.mode_priorite.setStyleSheet("font-weight: bold; color: white; background: transparent;")
        self.mode_group.addButton(self.mode_priorite)
        
        self.mode_aleatoire = QRadioButton("Répartition aléatoire par rég/prov")
        self.mode_aleatoire.setStyleSheet("font-weight: bold; color: white; background: transparent;")
        self.mode_group.addButton(self.mode_aleatoire)
        
       
        config_layout.addWidget(config_title)
        config_layout.addWidget(priority_label)
        config_layout.addWidget(self.mode_priorite)
        config_layout.addWidget(self.mode_aleatoire)
      
        config_section.setLayout(config_layout)
        
        # Section Actions
        actions_section = QFrame()
        actions_section.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        self.btn_traiter = ModernButton("Lancer la Répartition", "#3498db")
        self.btn_traiter.clicked.connect(self.lancer_repartition)
        
        self.btn_export = ModernButton("Résultats")
        self.btn_export.clicked.connect(self.show_resultats)
        self.btn_export.setEnabled(True)
        
        actions_layout.addWidget(self.btn_traiter)
        actions_layout.addWidget(self.btn_export)
        actions_section.setLayout(actions_layout)
        
        sidebar_layout.addWidget(import_section)
        sidebar_layout.addWidget(config_section)
        sidebar_layout.addWidget(actions_section)
        sidebar.setLayout(sidebar_layout)
        layout.addWidget(sidebar)

    def create_main_content(self, layout):
        main_content = QFrame()
        main_content.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Création du stack widget pour gérer les différentes pages
        self.stack_widget = QStackedWidget()
        
        # Page principale (tableau de bord)
        dashboard_page = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_page)
        
        # Titre
        title = QLabel("Tableau de Bord")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; background: transparent;")

        # Encapsuler le titre dans un QFrame pour appliquer le même fond que le header
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_layout.addWidget(title)
        title_frame.setLayout(title_layout)
        
        # Cartes statistiques
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: transparent;")
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.card_candidats = CardWidget("Candidats", "0", "#3498db")
        self.card_salles = CardWidget("Salles", "0", "#e67e22")
        self.card_status = CardWidget("Status", "En attente", "#f1c40f")
        
        stats_layout.addWidget(self.card_candidats)
        stats_layout.addWidget(self.card_salles)
        stats_layout.addWidget(self.card_status)
        stats_frame.setLayout(stats_layout)
        
        # Zone de résultats
        results_frame = QFrame()
        results_frame.setStyleSheet("background-color: transparent;")
        
        results_layout = QVBoxLayout()
        
        results_title = QLabel("Aperçu des Résultats")
        results_title.setFont(QFont("Arial", 14,QFont.Weight.Bold))
        
        # Boutons d'affichage
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        
        self.btn_show_candidats = ModernButton("Afficher Candidats", "#3498db", "#2980b9")
        self.btn_show_candidats.clicked.connect(self.afficher_candidats)
        self.btn_show_candidats.setEnabled(False)
        
        self.btn_show_salles = ModernButton("Afficher Salles", "#e67e22", "#d35400")
        self.btn_show_salles.clicked.connect(self.afficher_salles)
        self.btn_show_salles.setEnabled(False)
        
        buttons_layout.addWidget(self.btn_show_candidats)
        buttons_layout.addWidget(self.btn_show_salles)
        buttons_layout.setSpacing(10)
        buttons_frame.setLayout(buttons_layout)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(50, 50, 60, 0.7);
                color: white;
            }
            QCheckBox, QRadioButton {
                color: #aaaaaa;
            }
        """)
        
        # Tableau pour l'affichage des résultats
        self.results_table = QTableWidget()
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(50, 50, 60, 0.7);
                color: white;
                border-radius: 5px;
                font-size: 13px;
                gridline-color: #394150;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
        # Empêcher l'édition des cellules
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setVisible(False)
        
        results_layout.addWidget(results_title)
        results_layout.addWidget(buttons_frame)
        results_layout.addWidget(self.results_text)
        results_layout.addWidget(self.results_table)
        results_frame.setLayout(results_layout)
        
        # Ajouter les widgets à la page du tableau de bord
        dashboard_layout.addWidget(title_frame)
        dashboard_layout.addWidget(stats_frame)
        dashboard_layout.addWidget(results_frame)
        
        # Ajouter la page du tableau de bord au stack widget
        self.stack_widget.addWidget(dashboard_page)
        
        main_layout.addWidget(self.stack_widget)
        main_content.setLayout(main_layout)
        layout.addWidget(main_content)
        
    def show_resultats(self):
        """Affiche la fenêtre des résultats"""
        resultats_dialog = ResultatsDialog(self)
        resultats_dialog.exec()

    def apply_dark_theme(self):
        """Applique le thème sombre à l'application"""
        dark_style = """
            QWidget {
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #808080;
            }
            QTextEdit {
                background-color: rgba(50, 50, 60, 0.7);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
            QCheckBox, QRadioButton {
                color: #aaaaaa;
                spacing: 8px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QTableWidget {
                gridline-color: #394150;
                selection-background-color: #2980b9;
            }
            QHeaderView::section {
                background-color: #3498db;
                padding: 5px;
                border: none;
            }
            QMessageBox {
                background-color: #2c3e50;
            }
        """
        self.setStyleSheet(dark_style)

    def import_file(self, file_type):
        if file_type == 'salles':
            dialog = CentresSallesEntryDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                salles_data = dialog.get_data()
                
                # Créer le DataFrame avec les types de données corrects
                self.df_salles = pd.DataFrame(salles_data)
                
                # Normaliser les noms de colonnes
                self.df_salles.columns = [col.strip().lower().replace('é', 'e').replace('è', 'e').replace('à', 'a') for col in self.df_salles.columns]
                
                # S'assurer que les colonnes climatise et camera restent des chaînes
                self.df_salles['climatise'] = self.df_salles['climatise'].astype(str)
                self.df_salles['camera'] = self.df_salles['camera'].astype(str)
                
                # Sauvegarder dans la base de données
                self.salles_db.save_salles(self.df_salles)
                
                self.nb_salles = len(self.df_salles)
                self.card_salles.update_value(self.nb_salles)
                self.btn_show_salles.setEnabled(True)
                self.info_salles.setText(f"✅ {self.nb_salles} salles saisies")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Sélectionner le fichier des {file_type}", 
            "", 
            "Excel/CSV files (*.xlsx *.csv);;All files (*.*)"
        )
        
        if file_path:
            try:
                
                if file_type == 'candidats':
                    self.fichier_candidats = file_path
                    filename = os.path.basename(file_path)
                    

                    # Correction : forcer l'utilisation de l'engine openpyxl pour Excel
                    if file_path.endswith('.xlsx'):
                        self.df_candidats = pd.read_excel(file_path, engine='openpyxl')
                    else:
                        # Import CSV avec gestion d'encodage
                        try:
                            self.df_candidats = pd.read_csv(file_path, encoding='utf-8')
                        except UnicodeDecodeError:
                            try:
                                self.df_candidats = pd.read_csv(file_path, encoding='latin1')
                            except Exception as e2:
                                raise Exception(f"Impossible de lire le fichier CSV en UTF-8 ou latin1 : {e2}")
                    
                    # Vérifier les cases vides
                    missing = []
                    for i, row in self.df_candidats.iterrows():
                        for j, value in enumerate(row):
                            if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                                col_name = self.df_candidats.columns[j]
                                missing.append(f"Ligne {i+2}, colonne '{col_name}'")
                    
                    # Sauvegarder dans la base de données si aucune case vide
                    if not missing:
                        try:
                            # Réinitialiser la base de données avant d'importer
                            self.candidats_db.reinitialiser_db()
                            self.candidats_db.save_candidats(self.df_candidats)
                            self.nb_candidats = len(self.df_candidats)
                            self.card_candidats.update_value(self.nb_candidats)
                            self.btn_show_candidats.setEnabled(True)
                            self.info_candidats.setText(f"✅ {self.nb_candidats} candidats importés")
                        except ValueError as e:
                            # Créer une boîte de dialogue personnalisée pour les erreurs de validation
                            error_dialog = QDialog(self)
                            error_dialog.setWindowTitle("Erreur de validation")
                            error_dialog.setStyleSheet("""
                                QDialog {
                                    background-color: rgba(30, 30, 40, 0.95);
                                    border-radius: 12px;
                                    border: 1px solid rgba(255, 255, 255, 0.2);
                                }
                                QLabel {
                                    color: white;
                                    background: transparent;
                                }
                                QTextEdit {
                                    background-color: rgba(20, 20, 30, 0.95);
                                    color: white;
                                    border: 1px solid rgba(255, 255, 255, 0.2);
                                    border-radius: 6px;
                                    font-size: 14px;
                                }
                            """)
                            error_dialog.setMinimumWidth(600)
                            
                            layout = QVBoxLayout(error_dialog)
                            
                            # Titre avec icône d'avertissement
                            title_layout = QHBoxLayout()
                            warning_icon = QLabel()
                            warning_icon.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning).pixmap(32, 32))
                            title_layout.addWidget(warning_icon)
                            title = QLabel("Impossible d'importer les candidats")
                            title.setStyleSheet("color: #e74c3c; font-size: 18px; font-weight: bold;")
                            title_layout.addWidget(title)
                            layout.addLayout(title_layout)
                            
                            # Message d'erreur scrollable
                            text_area = QTextEdit()
                            text_area.setReadOnly(True)
                            text_area.setText(str(e))
                            text_area.setStyleSheet("""
                                QTextEdit {
                                    background-color: rgba(40, 44, 52, 1);
                                    color: #ffffff;
                                    font-size: 14px;
                                    font-weight: normal;
                                    border: 2px solid rgba(255, 255, 255, 0.2);
                                    border-radius: 6px;
                                    padding: 15px;
                                    selection-background-color: #3498db;
                                    selection-color: white;
                                }
                            """)
                            text_area.setMinimumHeight(200)
                            layout.addWidget(text_area)
                            
                            # Message d'aide
                            help_text = QLabel("Veuillez corriger ces erreurs dans votre fichier avant de réessayer l'importation.")
                            help_text.setStyleSheet("color: #bdc3c7; font-size: 13px;")
                            help_text.setWordWrap(True)
                            layout.addWidget(help_text)
                            
                            # Bouton Fermer
                            btn_close = QPushButton("Fermer")
                            btn_close.setStyleSheet("""
                                QPushButton {
                                    background-color: #e74c3c;
                                    color: white;
                                    border-radius: 6px;
                                    padding: 8px 24px;
                                    font-weight: bold;
                                    font-size: 14px;
                                }
                                QPushButton:hover {
                                    background-color: #c0392b;
                                }
                            """)
                            btn_close.clicked.connect(error_dialog.accept)
                            layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
                            
                            error_dialog.exec()
                            return
                        except Exception as e:
                            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
                            return
                    else:
                        msg = "Des cases vides ont été détectées dans le fichier des candidats.\n\n" + "\n".join(missing)
                        # QDialog personnalisé pour l'erreur
                        error_dialog = QDialog(self)
                        error_dialog.setWindowTitle("Erreur - Cases vides détectées")
                        error_dialog.setStyleSheet("""
                           QDialog {
                            background-color: rgba(40, 40, 50, 0.7);
                            border-radius: 12px;
                        }
                         """)
                        error_dialog.setMinimumWidth(500)
                        layout = QVBoxLayout(error_dialog)
                        title = QLabel("<span style='color:#3498db; font-size:18px; font-weight:bold;'>Des cases vides ont été détectées</span>")
                        title.setTextFormat(Qt.TextFormat.RichText)
                        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        layout.addWidget(title)
                        # Texte scrollable
                        from PyQt6.QtWidgets import QTextEdit
                        text_area = QTextEdit()
                        text_area.setReadOnly(True)
                        text_area.setText(msg)
                        text_area.setStyleSheet("""
                        QTextEdit {
                            background: transparent;
                            color: white;
                            font-size: 15px;
                            border: none;
                         }
                       """)
                        text_area.setMinimumHeight(200)
                        layout.addWidget(text_area)
                       # Bouton fermer
                        btn_close = QPushButton("Fermer")
                        btn_close.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            border-radius: 6px;
                            padding: 8px 24px;
                            font-weight: bold;
                            font-size: 15px;
                        }
                        QPushButton:hover {
                            background-color: #217dbb;
                        }
                       """)
                        btn_close.clicked.connect(error_dialog.accept)
                        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
                        error_dialog.exec()
                        return

                elif file_type == 'salles':
                    self.fichier_salles = file_path
                    filename = os.path.basename(file_path)
                    self.info_salles.setText(f"✅ {filename}")

                    if file_path.endswith('.xlsx'):
                        self.df_salles = pd.read_excel(file_path, engine='openpyxl')
                    else:
                        self.df_salles = pd.read_csv(file_path)
                    
                    # Réinitialiser la base de données avant d'importer
                    self.salles_db.reinitialiser_db()
                    # Sauvegarder les nouvelles données
                    self.salles_db.save_salles(self.df_salles)
                    self.nb_salles = len(self.df_salles)
                    self.card_salles.update_value(self.nb_salles)
                    self.btn_show_salles.setEnabled(True)

            except Exception as e:
                # Appliquer un style personnalisé aux QMessageBox pour les erreurs
                error_box = QMessageBox()
                error_box.setStyleSheet("""
                    QMessageBox {
                        background-color: rgba(30, 30, 40, 0.7);
                        color: white;
                        font-size: 14px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                    }
                    QLabel {
                        color: white;
                        font-weight: bold;
                        background: transparent;
                    }
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border-radius: 6px;
                        padding: 8px 20px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                    QTextEdit {
                        background-color: rgba(20, 20, 30, 0.7);
                        color: white;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 4px;
                        padding: 8px;
                    }
                """)
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setWindowTitle("Erreur")
                error_box.setText(f"Erreur lors de l'importation : {str(e)}\n\nAssurez-vous que le fichier n'est pas ouvert dans Excel et que le format est correct.")
                error_box.exec()

    def afficher_candidats(self):
        if self.df_candidats is not None:
            try:
                self.results_table.clearSpans()
                self.results_text.setVisible(False)
                self.results_table.setVisible(True)
                self.results_table.clear()
                self.results_table.setRowCount(len(self.df_candidats))
                self.results_table.setColumnCount(len(self.df_candidats.columns))
                self.results_table.setHorizontalHeaderLabels([str(col) for col in self.df_candidats.columns])
                self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                for i, row in self.df_candidats.iterrows():
                    for j, value in enumerate(row):
                        col_name = self.df_candidats.columns[j].lower()
                        display_value = value
                        if isinstance(value, str) and ("-" in value and ":" in value):
                            try:
                                display_value = value.split()[0]
                            except Exception:
                                display_value = value
                        elif (col_name in ["annee", "année", "anneenaissance", "annee_naissance"] or ("annee" in col_name or "année" in col_name)) and isinstance(value, float):
                            if pd.isna(value):
                                display_value = ""
                            else:
                                display_value = str(int(value))
                        elif hasattr(value, 'strftime'):
                            display_value = value.strftime('%d-%m-%Y')
                        item = QTableWidgetItem(str(display_value))
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.results_table.setItem(i, j, item)
                self.results_table.resizeColumnsToContents()
                self.results_table.resizeRowsToContents()
                self.results_table.scrollToTop()
                for i in range(self.results_table.rowCount()):
                    self.results_table.setRowHeight(i, 38)
            except Exception as e:
                self.results_table.setVisible(False)
                self.results_text.setVisible(True)
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la lecture : {str(e)}")

    def afficher_salles(self):
        """Affiche les salles dans le tableau avec des statistiques"""
        if self.df_salles is not None and not self.df_salles.empty:
            try:
                # Réinitialiser le tableau
                self.results_table.clearSpans()
                self.results_table.clear()
                self.results_text.setVisible(False)
                self.results_table.setVisible(True)
                
                # Créer une copie du DataFrame pour ne pas modifier l'original
                df = self.df_salles.copy()
                
                # Standardiser les noms de colonnes
                df = df.rename(columns={
                    "Centres d'examen": 'centre',
                    "Locaux d'examen": 'nom',
                    "Capacité": 'capacite',
                    "Type": 'type',
                    "Climatisé": 'climatise',
                    "Camera": 'camera'
                })
                
                # S'assurer que les capacités sont des nombres
                df['capacite'] = pd.to_numeric(df['capacite'], errors='coerce')
                
                centres = df['centre'].unique()
                
                # Préparer le tableau
                self.results_table.clear()
                self.results_table.setRowCount(len(df))
                self.results_table.setColumnCount(8)
                self.results_table.setHorizontalHeaderLabels([
                    "Centre", "Nom de la salle", "Capacité", "Climatisé", 
                    "Caméra", "Type", "Total Centre", "Total Grandes Salles"
                ])
                
                row_idx = 0
                for centre in centres:
                    centre_df = df[df['centre'] == centre]
                    total = centre_df['capacite'].sum()
                    total_grande = centre_df[centre_df['type'] == 'Grande']['capacite'].sum()
                    n_salles = len(centre_df)
                    
                    for i, (_, salle) in enumerate(centre_df.iterrows()):
                        # Centre (première colonne, fusionnée)
                        if i == 0:
                            centre_item = QTableWidgetItem(centre)
                            centre_item.setBackground(QBrush(QColor(40, 40, 50)))
                            centre_item.setForeground(QBrush(QColor("white")))
                            centre_item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                            centre_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.results_table.setItem(row_idx, 0, centre_item)
                            if n_salles > 1:
                                self.results_table.setSpan(row_idx, 0, n_salles, 1)
                        
                            # Totaux (fusionnés aussi)
                            total_item = QTableWidgetItem(str(int(total)))
                            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.results_table.setItem(row_idx, 6, total_item)
                            if n_salles > 1:
                                self.results_table.setSpan(row_idx, 6, n_salles, 1)
                                
                            total_grande_item = QTableWidgetItem(str(int(total_grande)))
                            total_grande_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.results_table.setItem(row_idx, 7, total_grande_item)
                            if n_salles > 1:
                                self.results_table.setSpan(row_idx, 7, n_salles, 1)
                        
                        # Informations de la salle
                        nom_item = QTableWidgetItem(str(salle['nom']))
                        nom_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if str(salle['type']).strip() == 'Petite':
                            nom_item.setForeground(QBrush(QColor("#FF0000")))
                        if str(salle['type']).strip() == 'Petite':
                            nom_item.setForeground(QBrush(QColor("#FF0000")))
                        self.results_table.setItem(row_idx, 1, nom_item)
                        
                        capacite_item = QTableWidgetItem(str(int(salle['capacite'])))
                        capacite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        # Si c'est une petite salle, mettre le texte en rouge
                        if str(salle['type']).strip() == 'Petite':
                            capacite_item.setForeground(QBrush(QColor("#FF0000")))
                        self.results_table.setItem(row_idx, 2, capacite_item)
                        
                        climatise_item = QTableWidgetItem(str(salle['climatise']))
                        climatise_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.results_table.setItem(row_idx, 3, climatise_item)
                        
                        camera_item = QTableWidgetItem(str(salle['camera']))
                        camera_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.results_table.setItem(row_idx, 4, camera_item)
                        
                        type_item = QTableWidgetItem(str(salle['type']))
                        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.results_table.setItem(row_idx, 5, type_item)
                        
                        row_idx += 1
                        
                self.results_table.resizeColumnsToContents()
                self.results_table.resizeRowsToContents()
                
                # Augmenter la hauteur des lignes
                for i in range(self.results_table.rowCount()):
                    self.results_table.setRowHeight(i, 38)
                    
            except Exception as e:
                self.results_table.setVisible(False)
                self.results_text.setVisible(True)
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'affichage : {str(e)}")

    def charger_donnees_db(self):
        """Charge les données depuis les bases de données"""
        try:
            self.card_status.update_value("Chargement...")
            
            # Charger les candidats depuis la base de données
            self.df_candidats = self.candidats_db.get_all_candidats()
            self.df_candidats = self.df_candidats.fillna('')  # Remplacer les NaN par des chaînes vides
            if self.df_candidats is not None and not self.df_candidats.empty:
                # S'assurer que les colonnes nécessaires existent
                colonnes_requises = ['Code', 'LastName', 'FirstName', 'region', 'province']
                colonnes_manquantes = [col for col in colonnes_requises if col not in self.df_candidats.columns]
                if colonnes_manquantes:
                    raise Exception(f"Colonnes manquantes dans la base candidats : {', '.join(colonnes_manquantes)}")
                
                # Nettoyer les données des candidats
                self.df_candidats['Code'] = self.df_candidats['Code'].astype(str)
                self.df_candidats['LastName'] = self.df_candidats['LastName'].str.strip()
                self.df_candidats['FirstName'] = self.df_candidats['FirstName'].str.strip()
                self.df_candidats['region'] = self.df_candidats['region'].str.strip()
                self.df_candidats['province'] = self.df_candidats['province'].str.strip()
                
                # Mettre à jour l'interface
                self.nb_candidats = len(self.df_candidats)
                self.card_candidats.update_value(self.nb_candidats)
                self.btn_show_candidats.setEnabled(True)
                self.info_candidats.setText(f"✅ {self.nb_candidats} candidats chargés")
            
            # Charger les centres et salles depuis la base de données
            centres = self.salles_db.get_all_centres()
            if centres is None or centres.empty:
                raise Exception("Aucun centre trouvé dans la base de données")
                
            all_salles = []
            for _, centre in centres.iterrows():
                salles = self.salles_db.get_salles_by_centre(centre['id'])
                if not salles.empty:
                    # Renommer les colonnes si nécessaire pour correspondre au format attendu
                    column_mapping = {
                        'Locaux d\'examen': 'nom',
                        'Capacité': 'capacite',
                        'Climatisé': 'climatise',
                        'Caméra': 'camera',
                        'Type': 'type'
                    }
                    
                    # Normaliser les noms de colonnes (enlever les accents et mettre en minuscules)
                    salles.columns = [col.strip().lower().replace('é', 'e').replace('è', 'e').replace('à', 'a') for col in salles.columns]
                    
                    # Renommer les colonnes selon le mapping
                    for old_col, new_col in column_mapping.items():
                        old_col_normalized = old_col.lower().replace('é', 'e').replace('è', 'e').replace('à', 'a')
                        if old_col_normalized in salles.columns:
                            salles = salles.rename(columns={old_col_normalized: new_col})
                    
                    # S'assurer que toutes les colonnes requises sont présentes
                    colonnes_requises = ['nom', 'capacite', 'climatise', 'camera', 'type']
                    colonnes_manquantes = [col for col in colonnes_requises if col not in salles.columns]
                    if colonnes_manquantes:
                        raise Exception(f"Colonnes manquantes pour le centre {centre['nom']} : {', '.join(colonnes_manquantes)}")
                    
                    # Ajouter le nom du centre
                    salles['centre'] = centre['nom']
                    all_salles.append(salles)
            
            if all_salles:
                self.df_salles = pd.concat(all_salles)
                
                # Standardiser les noms de colonnes
                self.df_salles = self.df_salles.rename(columns={
                    'Centre': 'Centre',
                    'Locaux d\'examen': 'Locaux d\'examen',
                    'Capacité': 'Capacité',
                    'Type': 'Type',
                    'Climatisé': 'Climatisé',
                    'Caméra': 'Caméra'
                })
                
                # Nettoyer et convertir les types de données
                self.df_salles['capacite'] = pd.to_numeric(self.df_salles['capacite'], errors='coerce')
                self.df_salles['climatise'] = self.df_salles['climatise'].astype(str)
                self.df_salles['camera'] = self.df_salles['camera'].astype(str)
                self.df_salles['type'] = self.df_salles['type'].astype(str)
                self.df_salles['nom'] = self.df_salles['nom'].str.strip()
                self.df_salles['centre'] = self.df_salles['centre'].str.strip()
                
                # Vérifier la validité des données
                salles_invalides = self.df_salles[self.df_salles['capacite'].isna()]
                if not salles_invalides.empty:
                    raise Exception(f"Capacités invalides détectées dans les salles: {', '.join(salles_invalides['nom'].tolist())}")
                    
                if self.df_salles['capacite'].min() <= 0:
                    salles_zero = self.df_salles[self.df_salles['capacite'] <= 0]['nom'].tolist()
                    raise Exception(f"Les salles suivantes ont une capacité nulle ou négative : {', '.join(salles_zero)}")
                
                # Mettre à jour l'interface
                self.nb_salles = len(self.df_salles)
                self.card_salles.update_value(self.nb_salles)
                self.card_status.update_value("OK ✅")
                self.btn_show_salles.setEnabled(True)
                self.info_salles.setText(f"✅ {self.nb_salles} salles chargées")
                
                # Afficher un résumé des données chargées
                print(f"Données chargées avec succès:")
                print(f"- {self.nb_candidats} candidats")
                print(f"- {self.nb_salles} salles dans {len(self.df_salles['centre'].unique())} centres")
                print(f"- Capacité totale: {self.df_salles['capacite'].sum()} places")
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des données: {str(e)}"
            print(error_msg)
            self.afficher_message_erreur("Erreur de chargement", error_msg)
            self.df_candidats = pd.DataFrame()
            self.df_salles = pd.DataFrame()
            self.card_status.update_value("Erreur ❌")

    def importer_candidats(self):
        """Importe les candidats depuis un fichier Excel et les sauvegarde dans la base de données"""
        try:
            fichier, _ = QFileDialog.getOpenFileName(
                self,
                "Sélectionner le fichier des candidats",
                "",
                "Fichiers Excel (*.xlsx *.xls);;CSV (*.csv)"
            )
            
            if fichier:
                if fichier.endswith('.csv'):
                    df = pd.read_csv(fichier)
                else:
                    df = pd.read_excel(fichier)
                
                # Sauvegarder dans la base de données
                self.candidats_db.save_candidats(df)
                
                # Mettre à jour les variables d'état
                self.fichier_candidats = fichier
                self.df_candidats = df
                self.nb_candidats = len(df)
                
                # Mettre à jour l'interface
                self.mettre_a_jour_stats()
                self.afficher_candidats()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"{self.nb_candidats} candidats ont été importés avec succès"
                )
                
        except Exception as e:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle("Erreur")
            error_box.setText(f"Erreur lors de l'importation : {str(e)}\n\nAssurez-vous que le fichier n'est pas ouvert dans Excel et que le format est correct.")
            error_box.exec()

    def importer_salles(self):
        """Importe les salles depuis un fichier Excel et les sauvegarde dans la base de données"""
        try:
            fichier, _ = QFileDialog.getOpenFileName(
                self,
                "Sélectionner le fichier des salles",
                "",
                "Fichiers Excel (*.xlsx *.xls);;CSV (*.csv)"
            )
            
            if fichier:
                if fichier.endswith('.csv'):
                    df = pd.read_csv(fichier)
                else:
                    df = pd.read_excel(fichier)
                
                # Normaliser les noms de colonnes
                df.columns = [col.strip().lower().replace('é', 'e').replace('è', 'e').replace('à', 'a') for col in df.columns]
                
                # Sauvegarder dans la base de données
                self.salles_db.save_salles(df)
                
                # Mettre à jour les variables d'état
                self.fichier_salles = fichier
                self.df_salles = df
                self.nb_salles = len(df)
                
                # Mettre à jour l'interface
                self.mettre_a_jour_stats()
                self.afficher_salles()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"{self.nb_salles} salles ont été importées avec succès"
                )
                
        except Exception as e:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle("Erreur")
            error_box.setText(f"Erreur lors de l'importation : {str(e)}\n\nAssurez-vous que le fichier n'est pas ouvert dans Excel et que le format est correct.")
            error_box.exec()

    def mettre_a_jour_stats(self):
        """Met à jour les statistiques affichées dans les cartes"""
        if self.df_candidats is not None:
            self.nb_candidats = len(self.df_candidats)
            self.card_candidats.update_value(self.nb_candidats)
            self.btn_show_candidats.setEnabled(True)

        if self.df_salles is not None:
            self.nb_salles = len(self.df_salles)
            self.card_salles.update_value(self.nb_salles)
            self.btn_show_salles.setEnabled(True)

    def afficher_message_erreur(self, titre, message):
        """Affiche une boîte de dialogue d'erreur"""
        QMessageBox.critical(self, titre, message)
        
    def afficher_message_succes(self, titre, message):
        """Affiche une boîte de dialogue de succès"""
        QMessageBox.information(self, titre, message)
        
    # Méthode pour lier la fonction importée de repartition.py
    def lancer_repartition(self):
        lancer_repartition(self)
        
    def exporter_resultats(self):
        """Exporte les résultats de la répartition vers un fichier Excel"""
        try:
            if self.resultats_repartition is None:
                self.afficher_message_erreur("Erreur", "Aucun résultat à exporter. Veuillez d'abord effectuer une répartition.")
                return
                
            fichier, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer les résultats",
                f"resultats_repartition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Fichiers Excel (*.xlsx)"
            )
            
            if fichier:
                # S'assurer que le fichier a l'extension .xlsx
                if not fichier.endswith('.xlsx'):
                    fichier += '.xlsx'
                    
                # Sauvegarder dans Excel
                self.resultats_repartition.to_excel(fichier, index=False)
                self.afficher_message_succes("Export réussi", f"Les résultats ont été exportés vers {fichier}")
                
        except Exception as e:
            self.afficher_message_erreur("Erreur d'export", f"Erreur lors de l'export : {str(e)}")

  