# Software Requirements Specification (SRS)  
**Project:** Fixed‑Wing UAV Design Assistant  
**Version:** 1.0  
**Author:** *[Your Name]*  
**Date:** 2026‑04‑23  

---

## Revision History

| Version | Date       | Author | Description |
|---------|------------|--------|-------------|
| 1.0     | 2026‑04‑23 | *[Your Name]* | Initial SRS draft |

---

## Table of Contents

1. [Introduction](#1-introduction)  
   1.1 [Purpose](#11-purpose)  
   1.2 [Scope](#12-scope)  
   1.3 [Definitions, Acronyms & Abbreviations](#13-definitions-acronyms--abbreviations)  
   1.4 [References](#14-references)  
2. [Overall Description](#2-overall-description)  
   2.1 [Product Perspective](#21-product-perspective)  
   2.2 [Product Functions](#22-product-functions)  
   2.3 [User Classes & Characteristics](#23-user-classes--characteristics)  
   2.4 [Operating Environment](#24-operating-environment)  
   2.5 [Design & Implementation Constraints](#25-design--implementation-constraints)  
   2.6 [Assumptions & Dependencies](#26-assumptions--dependencies)  
3. [System Features](#3-system-features)  
   3.1 [Payload Input & Validation](#31-payload-input--validation)  
   3.2 [Aerodynamic & Structural Calculations](#32-aerodynamic--structural-calculations)  
   3.3 [Design Parameter Suggestions](#33-design-parameter-suggestions)  
   3.4 [Report Generation](#34-report-generation)  
   3.5 [Safety & Regulatory Checks](#35-safety--regulatory-checks)  
   3.6 [User Interface](#36-user-interface)  
   3.7 [Data Management](#37-data-management)  
   3.8 [Export & Integration](#38-export--integration)  
4. [External Interface Requirements](#4-external-interface-requirements)  
   4.1 [User Interfaces](#41-user-interfaces)  
   4.2 [Hardware Interfaces](#42-hardware-interfaces)  
   4.3 [Software Interfaces](#43-software-interfaces)  
   4.4 [Communication Interfaces](#44-communication-interfaces)  
5. [System Requirements](#5-system-requirements)  
   5.1 [Functional Requirements](#51-functional-requirements)  
   5.2 [Non‑Functional Requirements](#52-non-functional-requirements)  
   5.3 [Performance Requirements](#53-performance-requirements)  
   5.4 [Safety Requirements](#54-safety-requirements)  
   5.5 [Security Requirements](#55-security-requirements)  
   5.6 [Usability Requirements](#56-usability-requirements)  
   5.7 [Reliability & Availability](#57-reliability--availability)  
   5.8 [Maintainability](#58-maintainability)  
   5.9 [Portability](#59-portability)  
6. [Other Requirements](#6-other-requirements)  
   6.1 [Data Formats & Standards](#61-data-formats--standards)  
   6.2 [Documentation](#62-documentation)  
7. [Appendices](#7-appendices)  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the functional and non‑functional requirements for the **Fixed‑Wing UAV Design Assistant (FWU‑DA)**. The software will allow aerospace engineers and hobbyists to generate preliminary design parameters for a fixed‑wing Unmanned Aerial Vehicle (UAV) based solely on a user‑specified total payload. The tool will perform aerodynamic, structural, and weight‑balance calculations, suggest design options, and produce a comprehensive design report.

### 1.2 Scope
The FWU‑DA is a desktop/web application that:
- Accepts a payload mass (kg) and optional constraints (e.g., maximum wingspan, cruise speed).
- Calculates required wing area, aspect ratio, lift‑to‑drag ratio, and other key parameters.
- Recommends airfoil families, wing geometry, and material choices.
- Generates a PDF/HTML report and stores design data in a local database.
- Provides a simple GUI and a command‑line interface for batch processing.

The tool is **not** a full‑scale CAD or simulation package; it is a *pre‑design* calculator that outputs design guidelines.

### 1.3 Definitions, Acronyms & Abbreviations
| Term | Definition |
|------|------------|
| UAV | Unmanned Aerial Vehicle |
| FWU‑DA | Fixed‑Wing UAV Design Assistant |
| SRS | Software Requirements Specification |
| L/D | Lift‑to‑Drag ratio |
| AoA | Angle of Attack |
| CL | Lift coefficient |
| CD | Drag coefficient |
| AR | Aspect Ratio |
| S | Wing area |
| b | Wingspan |
| c | Mean chord |
| ρ | Air density |
| V | Cruise velocity |
| W | Total weight (payload + airframe + fuel) |
| MTOW | Maximum Take‑Off Weight |
| FAA | Federal Aviation Administration |
| EASA | European Union Aviation Safety Agency |

### 1.4 References
| ID | Title | Source |
|----|-------|--------|
| R1 | *NASA – Aircraft Performance* | https://www.nasa.gov |
| R2 | *EASA CS‑23 – Certification Specifications for Normal, Utility, Aerobatic and Commuter Category Aeroplanes* | https://www.easa.europa.eu |
| R3 | *FAA Advisory Circular 20‑1075 – UAV Design* | https://www.faa.gov |
| R4 | *ISO 9001:2015 – Quality Management Systems* | ISO |

---

## 2. Overall Description

### 2.1 Product Perspective
FWU‑DA is a **stand‑alone** application that can be installed on Windows, macOS, and Linux. It will be built using Python 3.11+ (backend) and a cross‑platform GUI framework (Qt/PySide or Tkinter). A lightweight SQLite database will store user profiles and design histories.

### 2.2 Product Functions
| Function | Description |
|----------|-------------|
| Payload entry | Accepts user input for payload mass and optional constraints. |
| Weight estimation | Calculates empty airframe weight using empirical rules of thumb. |
| Aerodynamic analysis | Computes required wing area, aspect ratio, and CL based on lift equation. |
| Structural sizing | Estimates spar and skin thickness using bending and shear formulas. |
| Material selection | Suggests composite or aluminum options based on weight and cost. |
| Report generation | Produces a printable PDF and an HTML view. |
| Data export | Exports design data to CSV, JSON, or CAD-compatible DXF. |
| Batch mode | Processes a CSV of payloads to generate multiple design reports. |

### 2.3 User Classes & Characteristics
| User Class | Characteristics |
|------------|-----------------|
| Aerospace Engineer | Experienced in UAV design, needs accurate calculations. |
| Hobbyist / Maker | Limited design knowledge, requires guided suggestions. |
| Academic Researcher | Needs batch processing and export for analysis. |
| Regulatory Officer | Uses reports to verify compliance. |

### 2.4 Operating Environment
| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11, macOS 12+, Ubuntu 20.04+ |
| CPU | 2 GHz dual‑core or higher |
| RAM | 4 GB minimum |
| Disk | 200 MB free space |
| GUI | Qt 6 / PySide6 or Tkinter |
| Libraries | NumPy, SciPy, Pandas, ReportLab, PyQt5/6 |

### 2.5 Design & Implementation Constraints
- Must run offline; no external API calls.
- All calculations must be deterministic and reproducible.
- The GUI must be responsive; calculation time < 5 s for a single payload.
- The software must comply with EASA CS‑23 and FAA AC 20‑1075 for design guidance.

### 2.6 Assumptions & Dependencies
- The user provides accurate payload mass.
- The UAV operates at sea‑level standard atmosphere unless overridden.
- No advanced CFD or finite‑element analysis is performed; empirical formulas are used.

---

## 3. System Features

### 3.1 Payload Input & Validation
- **Input Fields**: Payload mass (kg), optional maximum wingspan (m), cruise speed (m/s), mission altitude (m).
- **Validation**: Range checks (e.g., payload > 0 kg, wingspan > 0 m). Error messages displayed in UI.

### 3.2 Aerodynamic & Structural Calculations
| Sub‑Feature | Description |
|-------------|-------------|
| Lift equation | \( W = \frac{1}{2} \rho V^2 S C_L \) |
| Aspect ratio selection | AR = \( \frac{b^2}{S} \) |
| CL range | 0.5–1.5 (user selectable) |
| Drag estimation | \( C_D = C_{D0} + k C_L^2 \) |
| Structural sizing | Bending moment \( M = \frac{W b}{8} \); spar thickness from \( \sigma = \frac{M}{S_{spar}} \) |
| Weight estimation | Empirical rule: \( W_{airframe} = 0.1 \times MTOW \) |

### 3.3 Design Parameter Suggestions
- **Wing span**: Suggested based on AR and user constraints.
- **Mean chord**: Derived from wing area and span.
- **Airfoil**: Recommend from a database (e.g., NACA 2412, 0012) based on CL and Reynolds number.
- **Material**: Composite (carbon fiber) vs. aluminum alloy (7075‑T6) with weight and cost estimates.

### 3.4 Report Generation
- **PDF**: Includes design tables, charts (lift‑drag curves), and a summary.
- **HTML**: Interactive view with embedded graphs (Plotly).
- **Report Sections**: Executive summary, assumptions, calculations, design recommendations, compliance checklist.

### 3.5 Safety & Regulatory Checks
- Verify that the design meets minimum stall speed (e.g., < 15 m/s).
- Check that the wing loading \( \frac{W}{S} \) is within acceptable limits for the chosen airframe class.
- Flag any parameters that violate CS‑23 or AC 20‑1075.

### 3.6 User Interface
- **Main Window**: Input panel, calculation button, results panel.
- **Tabs**: “Design Parameters”, “Graphs”, “Report”.
- **Accessibility**: Keyboard navigation, high‑contrast mode.

### 3.7 Data Management
- **Local DB**: SQLite storing user profiles, design history, and custom airfoil data.
- **Import/Export**: CSV for batch payload lists; JSON for configuration.

### 3.8 Export & Integration
- **DXF**: Basic wing outline for CAD import.
- **CSV**: All numeric results for spreadsheet analysis.
- **API**: Optional REST endpoint for integration with other tools (e.g., simulation suites).

---

## 4. External Interface Requirements

### 4.1 User Interfaces
- **GUI**: Responsive, cross‑platform, with tooltips and help dialogs.
- **CLI**: `fwu-da --payload 5.0 --output design_report.pdf`.

### 4.2 Hardware Interfaces
- None beyond standard computer peripherals.

### 4.3 Software Interfaces
- **Python 3.11+** runtime.
- **NumPy/SciPy** for numerical calculations.
- **Pandas** for data handling.
- **ReportLab** for PDF generation.
- **Plotly** or **Matplotlib** for charts.

### 4.4 Communication Interfaces
- None required; all processing is local.

---

## 5. System Requirements

### 5.1 Functional Requirements
| FR ID | Description | Priority |
|-------|-------------|----------|
| FR‑001 | Accept payload mass input (kg). | High |
| FR‑002 | Validate input ranges. | High |
| FR‑003 | Compute wing area \(S\) using lift equation. | High |
| FR‑004 | Suggest wing span \(b\) and mean chord \(c\). | High |
| FR‑005 | Estimate airframe weight \(W_{airframe}\). | Medium |
| FR‑006 | Generate lift‑drag curve. | Medium |
| FR‑007 | Produce PDF/HTML report. | High |
| FR‑008 | Export design data to CSV/JSON. | Medium |
| FR‑009 | Batch process CSV of payloads. | Low |
| FR‑010 | Flag design violations against CS‑23/AC 20‑1075. | High |

### 5.2 Non‑Functional Requirements
| NFR ID | Description | Target |
|--------|-------------|--------|
| NFR‑001 | Response time for single calculation < 5 s. | 5 s |
| NFR‑002 | Memory usage < 200 MB. | 200 MB |
| NFR‑003 | 99.9 % uptime for local installation. | 99.9 % |
| NFR‑004 | UI must be usable on 1920×1080 resolution. | 1920×1080 |
| NFR‑005 | Software must be available under MIT license. | MIT |

### 5.3 Performance Requirements
- Calculations must be accurate to within ±1 % of standard reference values.
- Report generation time < 10 s for a single design.

### 5.4 Safety Requirements
- All design outputs must include a safety margin of 1.5× for structural loads.
- Stall speed calculation must be displayed; if > 15 m/s, a warning is shown.

### 5.5 Security Requirements
- No external network connections; all data stored locally.
- User data encrypted at rest using AES‑256 if password protection is enabled.

### 5.6 Usability Requirements
- First‑time user wizard guiding through input steps.
- Context‑sensitive help for each parameter.
- Exported reports must be printable on A4.

### 5.7 Reliability & Availability
- Application must recover gracefully from crashes; last session data should be preserved.

### 5.8 Maintainability
- Codebase must follow PEP‑8 style guide.
- Unit tests covering ≥90 % of calculation logic.
- Documentation generated with Sphinx.

### 5.9 Portability
- Must run on Windows 10/11, macOS 12+, Ubuntu 20.04+.
- No platform‑specific dependencies beyond the Python runtime.

---

## 6. Other Requirements

### 6.1 Data Formats & Standards
- **CSV**: Standard comma‑separated values with header row.
- **JSON**: For configuration and export.
- **DXF**: AutoCAD DXF R2010 for wing outline.
- **PDF**: ISO 32000‑1 compliant.

### 6.2 Documentation
- User manual (PDF) with screenshots.
- API reference (if applicable).
- Developer guide with architecture diagram.

---

## 7. Appendices

### 7.1 Sample Calculation Flow
1. **Input**: Payload = 5 kg, Cruise speed = 30 m/s, Max wingspan = 2 m.
2. **Assumptions**: Sea‑level density \(ρ = 1.225 kg/m³\), CL = 1.2.
3. **Compute**: \(S = \frac{W}{0.5 ρ V^2 C_L}\).
4. **Result**: \(S ≈ 0.45 m²\).
5. **AR**: \(AR = \frac{b^2}{S} = \frac{2^2}{0.45} ≈ 8.9\).
6. **Report**: Includes all intermediate steps.

### 7.2 Glossary
- **Wing Loading**: \( \frac{W}{S} \) (kg/m²).
- **Aspect Ratio**: \( \frac{b^2}{S} \).

### 7.3 Future Enhancements
- Integration with CFD tools for refined lift/drag.
- 3‑D CAD export (STEP, IGES).
- Cloud sync for design history.

--- 

*End of SRS.*