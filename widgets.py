from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import Qt
import os

class BackgroundWidget(QWidget):
    """Widget avec image de fond"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_pixmap = None
        self.load_background_image()
    
    def load_background_image(self):
        """Charge l'image de fond"""
        background_path = os.path.join(os.path.dirname(__file__), "assets", "img.jpg")
        if os.path.exists(background_path):
            self.background_pixmap = QPixmap(background_path)
        else:
            self.create_default_background()
    
    def create_default_background(self):
        """Crée une image de fond par défaut"""
        pixmap = QPixmap(1600, 900)
        painter = QPainter(pixmap)
        gradient = QLinearGradient(0, 0, 1600, 900)
        gradient.setColorAt(0, QColor(26, 26, 46))
        gradient.setColorAt(1, QColor(22, 33, 62))
        painter.fillRect(pixmap.rect(), QBrush(gradient))
        painter.end()
        self.background_pixmap = pixmap
    
    def paintEvent(self, event):
        """Dessine l'image de fond"""
        painter = QPainter(self)
        if self.background_pixmap:
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_pixmap)
        super().paintEvent(event)

class CardWidget(QFrame):
    """Widget de carte moderne"""
    def __init__(self, title, value, color="#3498db"):
        super().__init__()
        self.setFixedSize(180, 100)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 50, 0.7);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        
        self.value_label = QLabel(str(value))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)
    
    def update_value(self, value):
        self.value_label.setText(str(value))

class ModernButton(QPushButton):
    """Bouton moderne avec style personnalisé"""
    def __init__(self, text, color="#3498db", hover_color="#2980b9", height=40):
        super().__init__(text)
        self.setFixedHeight(height)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)

class CentresSallesEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.salles_db = parent.salles_db
        self.setWindowTitle("Gestion des Centres et Salles")
        self.setMinimumWidth(1200)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(30, 30, 40, 0.95);
            }
            QLabel {
                color: white;
            }
            QTableWidget {
                background-color: rgba(40, 44, 52, 1);
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                color: white;
            }
        """)

        layout = QVBoxLayout(self)

        # Titre
        title = QLabel("Gestion des Centres d'Examen et de leurs Salles")