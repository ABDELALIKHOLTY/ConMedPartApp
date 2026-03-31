# 🏥 ConMedPartApp

<div align="center">
![Logo](assets/iconapp_512.png)

### **Intelligent Medical Candidate Distribution & Management System**




*Transform your examination planning from 15-20 hours to just 5-10 minutes*

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-Modern%20GUI-green?style=for-the-badge&logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue?style=for-the-badge&logo=sqlite)](https://www.sqlite.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-purple?style=for-the-badge)](https://github.com/ABDELALIKHOLTY/ConMedPartApp)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()

</div>

---

## 📌 Table of Contents
- [About](#-about)
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 About

**ConMedPartApp** is a desktop application designed to manage and distribute candidates across exam rooms. It enables institutions to automate the distribution process that was previously manual and time-consuming.

### Use Cases:
- 🏫 Manage candidates for entrance exams
- 📍 Assign exam rooms
- 📄 Generate documents (displays, attendance lists)
- 📊 Multi-center management

---

## ✨ Features

### 👥 Candidate Management
- ✅ Import candidate lists (CSV/Excel)
- ✅ Display and manage candidates in interface
- ✅ View details: Code, Name, First Name, region, province, languages
- ✅ Secure storage in SQLite database

### 🏫 Room Configuration
- ✅ Create exam centers
- ✅ Add rooms per center
- ✅ Define room capacity
- ✅ Classify rooms by type
- ✅ View total capacity in real-time

### 📍 Candidate Distribution
- ✅ Automatically distribute candidates to rooms
- ✅ Check total available capacity
- ✅ Manage constraints (capacity, room type)
- ✅ Display distribution results

### 📄 Document Generation
- ✅ **Display** : Candidate lists by room (PDF)
- ✅ **Attendance** : Attendance sheets per room (PDF)
- ✅ Generate documents for all centers or specific center
- ✅ Professional documents ready to print

### 💾 Data Management
- ✅ Automatic database backup
- ✅ Three separate SQLite databases (candidates, rooms, distribution)
- ✅ Load and reuse saved data

---

## 🚀 Installation

### Requirements
- Python 3.8+
- pip
- Windows, Linux or macOS

### Installation Steps

**1. Clone the project**
```bash
git clone https://github.com/ABDELALIKHOLTY/ConMedPartApp.git
cd ConMedPartApp
```

**2. Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Launch application**
```bash
python main.py
```

---

## 📚 Project Structure

```
ConMedPartApp/
│
├── main.py                      # Entry point
├── dashboard.py                 # Main interface
├── repartition.py              # Distribution logic
├── resultats.py                # PDF document generation
├── salles.py                   # Room management
├── widgets.py                  # Custom components
│
├── database/                   # Database layer
│   ├── candidats_db.py        # Candidate management
│   ├── salles_db.py           # Room management
│   ├── repartition_db.py      # Distribution history
│   └── *.db                   # SQLite files
│
├── assets/                     # Resources
│   ├── iconapp_512.png        # App icon
│   ├── Logofmpf.png           # Institution logo
│   └── img.jpg                # UI images
│
│ 
│   
│   
│
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── LICENSE                   # MIT License
```

---

## 🎮 Usage

### Standard Workflow

#### Step 1️⃣ : Configure Rooms
1. Open the application
2. Go to **"Rooms"** in the menu
3. Add a center (ex: "Center Fes")
4. Add rooms with:
   - Name (ex: "Room A1")
   - Capacity (number of seats)
   - Type (ex: "Normal", "Accessible")
5. Save

#### Step 2️⃣ : Import Candidates
1. Go to **"Candidates"**
2. Import CSV/Excel file with columns:
   - Code (candidate ID)
   - LastName (Name)
   - FirstName (First Name)
   - region (Region)
   - province (Province)
   - langues (Languages)
3. Data is automatically saved

#### Step 3️⃣ : Launch Distribution
1. Go to **"Distribution"**
2. Verify that:
   - Candidates are imported ✓
   - Rooms are configured ✓
   - Total capacity ≥ number of candidates ✓
3. Click **"Start distribution"**
4. Check results

#### Step 4️⃣ : Generate Documents
1. Go to **"Results"**
2. Select center
3. Generate:
   - **Display** : Candidate display by room (PDF)
   - **Attendance** : Attendance sheet (PDF)
4. PDFs are generated and ready to print

---

## 📊 Technologies Used

| Technology | Usage |
|-----------|-------|
| **Python 3.8+** | Programming language |
| **PyQt6** | Graphical interface |
| **SQLite3** | Database |
| **Pandas** | Data processing |
| **ReportLab** | PDF generation |
| **Pillow** | Image processing |

---

## ⚙️ Data Formats

### Candidate File (CSV/Excel)
```
Code,LastName,FirstName,region,province,langues
001,Dupont,Jean,Fès,Province Fès,FR
002,Martin,Marie,Marrakech,Province Marrakech,FR AR
```

### Room Configuration
- Add via interface
- Save in database

---

## 🔧 Troubleshooting

### Application won't start
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Error: "Database locked"
```bash
# Close all app instances
# Delete journal files
rm database/*.db-journal
```

### Rooms won't add
- Verify that you created a center first
- Save after each addition

### PDF generation fails
- Verify ReportLab is installed: `pip install reportlab`
- Check folder write permissions

---

## 🔒 Data Storage

- **Local Storage** : All data stored in SQLite database on your machine
- **Privacy** : No data sent to external servers
- **Backup** : .db files are in `database/` folder



---

## 👨‍💼 Author

**ABDELALI KHOLTY**






### Contact
- GitHub: [ABDELALIKHOLTY](https://github.com/ABDELALIKHOLTY)
- Email: Abdelalikholty@gmail.com
- LinkedIn: www.linkedin.com/in/abdelalikholty


## 📊 Project Status

- Current Version: 1.0.0
- Last Updated: August 2025
- Status: Active Development





