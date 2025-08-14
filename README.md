# ConMedPartApp 🏥

<div align="center">

![Logo](assets/iconapp_512.png)

A desktop application for managing and distributing medical candidates.

</div>

## 📋 About

ConMedPartApp is a sophisticated desktop application engineered to streamline the management and distribution of candidates in the medical sector. This comprehensive solution offers an intuitive user interface built with PyQt6, enabling efficient administration of medical examinations and competitions.

### Core Objectives:

- Automate candidate distribution in examination rooms using advanced algorithms
- Maximize space utilization while maintaining optimal testing conditions
- Ensure fair and organized distribution of candidates
- Streamline administrative workflows and reduce manual effort
- Generate comprehensive documentation and reports instantly

### Key Benefits:

- **Time Efficiency**: Reduce planning time by up to 80%
- **Error Prevention**: Automated checks and validations
- **Resource Optimization**: Smart room allocation algorithms
- **Data Security**: Robust SQLite database implementation
- **User-Friendly**: Intuitive interface requiring minimal training

The application is developed in Python with a modular architecture, ensuring long-term stability, maintainability, and easy updates.

## ✨ Features

- 📊 **Advanced Dashboard Interface**:
  - Real-time system status monitoring
  - Quick access to all major functions
  - Customizable views and layouts
  - Comprehensive statistics and analytics
  - User activity tracking

- 👥 **Complete Candidate Management**:
  - Add, modify, and remove candidates
  - Bulk import/export of candidate data
  - Advanced search and filtering capabilities
  - Secure information storage
  - Candidate history tracking
  - Custom field support for additional data

- 🏫 **Examination Room Management**:
  - Room capacity configuration
  - Proctor assignment system
  - Availability scheduling
  - Room layout customization
  - Equipment and facilities tracking
  - Accessibility considerations

- 📍 **Intelligent Distribution System**:
  - Smart distribution algorithm
  - Capacity constraint management
  - Space optimization
  - Custom distribution rules
  - Conflict detection and resolution
  - Manual override capabilities

- 📝 **Comprehensive Results Generation**:
  - Professional PDF exports
  - Detailed room plans
  - Statistical reports
  - Custom report templates
  - Batch processing support


- 💾 **Robust Database Integration**:
  - High-performance SQLite implementation
  - Automatic data backup
  - Data integrity checks
  - Transaction management
  - Version control for data changes
  - Easy database maintenance

## 🚀 Installation Guide

### Prerequisites
- Python 3.x (3.8 or higher recommended)
- Git
- Windows, Linux, or macOS
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space

### Step-by-Step Installation

1. Clone the repository:
```bash
git clone https://github.com/ABDELALIKHOLTY/ConMedPartApp.git
cd ConMedPartApp
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/macOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify installation:
```bash
python -c "import PyQt6; import pandas; import reportlab; print('All dependencies installed successfully!')"
```

### Building from Source

To create a standalone executable:
```bash
python build_exe.py
```

The executable will be available in the `build/ConMedPartApp` directory.

### Troubleshooting

If you encounter any issues:
1. Ensure all prerequisites are met
2. Check Python version compatibility
3. Update pip: `python -m pip install --upgrade pip`
4. Clear pip cache: `pip cache purge`
5. Install individual dependencies if needed

## 🎯 Usage Guide

### Getting Started:

```bash
python main.py
```

### Detailed User Guide:

1. **Initial Setup**
   - Launch the application
   - Configure system preferences
   - Set up user permissions if needed
   - Verify database connectivity

2. **Candidate Management**
   - Individual candidate entry with validation
   - Bulk import via Excel/CSV files
   - Advanced search and filtering
   - Candidate information updates
   - History tracking and audit logs
   - Data export capabilities

3. **Room Configuration**
   - Define available examination rooms
   - Set room capacities and constraints
   - Assign proctors and staff
   - Configure room layouts
   - Set equipment requirements
   - Define accessibility parameters

4. **Automatic Distribution Process**
   - Initialize the distribution algorithm
   - Set distribution parameters
   - Review preliminary assignments
   - Handle special cases and exceptions
   - Manual adjustments if needed
   - Finalize distributions

5. **Document Generation**
   - Generate room allocation lists
   - Create detailed room plans
   - Export proctor assignments
   - Generate statistical reports
   - Create custom reports
   - Batch export capabilities

6. **System Maintenance**
   - Database backup procedures
   - Data integrity checks
   - System performance optimization
   - User management
   - Log file management
   - Software updates

## 🛠️ Technology Stack

### Core Technologies
- **Python** - Primary programming language
- **PyQt6** - Professional GUI Framework
  - Custom widgets
  - Responsive layouts
  - Modern design elements
  - Event-driven architecture

### Database Management
- **SQLite** - Embedded database
  - ACID compliance
  - Transaction support
  - Concurrent access handling
  - Data integrity protection

### Data Processing
- **Pandas** - Data manipulation and analysis
  - High-performance data structures
  - Statistical operations
  - Data import/export capabilities
  - Data transformation tools

### Document Generation
- **ReportLab** - PDF generation
  - Custom templates
  - Dynamic content generation
  - Professional formatting
  - Multi-page support

### Image Processing
- **Pillow** - Image handling
  - Format conversion
  - Image optimization
  - Thumbnail generation
  - Visual asset management

## 📁 Project Structure

```
ConMedPartApp/
├── assets/                # Graphic and media resources
│   ├── iconapp_512.png   # Application icon
│   ├── img.jpg           # UI images
│   ├── Logofmpf.png      # Organization logo
│   └── logopdf.jpg       # PDF template resources
│
├── database/             # Database management
│   ├── candidats_db.py   # Candidate database operations
│   ├── repartition_db.py # Distribution database operations
│   ├── salles_db.py      # Room database operations
│   ├── candidats.db      # Candidate SQLite database
│   ├── repartition.db    # Distribution SQLite database
│   └── salles.db        # Room SQLite database
│
├── build/               # Build and distribution files
│   └── ConMedPartApp/   # Compiled application
│
├── main.py             # Application entry point
├── dashboard.py        # Main interface and control logic
├── repartition.py      # Distribution algorithms
├── resultats.py        # Results processing and generation
├── salles.py          # Room management logic
├── widgets.py         # Custom UI components
├── build_exe.py       # Build script for executable
└── requirements.txt    # Project dependencies
```

### Component Details:

- **main.py**: Application bootstrapping and initialization
- **dashboard.py**: Core UI and business logic implementation
- **repartition.py**: Advanced distribution algorithms
- **resultats.py**: Comprehensive reporting system
- **salles.py**: Room management and optimization
- **widgets.py**: Reusable UI components library
- **build_exe.py**: Production build configuration

## 🤝 Contributing

We welcome contributions to ConMedPartApp! Here's how you can help:

### Ways to Contribute
- Report bugs and issues
- Suggest new features
- Improve documentation
- Submit pull requests
- Share feedback

### Development Process
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your fork
5. Submit a pull request

### Code Standards
- Follow PEP 8 guidelines
- Write comprehensive docstrings
- Maintain test coverage
- Keep commits atomic
- Use meaningful commit messages

## 🔒 Security

- All data is stored locally
- SQLite database encryption
- Secure password handling
- Regular security updates
- Access control implementation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Author & Maintainers

### Lead Developer
- **ABDELALI KHOLTY**
  - Project Architecture
  - Core Development
  - Technical Documentation

### Contact
- GitHub: [@ABDELALIKHOLTY](https://github.com/ABDELALIKHOLTY)
- Email: Abdelalikholty@gmail.com
- LinkedIn: www.linkedin.com/in/abdelalikholty


## 📊 Project Status

- Current Version: 1.0.0
- Last Updated: August 2025
- Status: Active Development

