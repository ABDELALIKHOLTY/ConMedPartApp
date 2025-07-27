from dashboard import *
import os

app = QApplication(sys.argv)

# Définir l'icône de l'application
icon_path = os.path.join(os.path.dirname(__file__), "assets", "iconapp_512.png")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))

window = ConMedPartApp()
window.show()
sys.exit(app.exec())