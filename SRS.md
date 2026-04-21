# Software Requirements Specification (SRS)  
**Project:** UAV Design & Construction Assistant  
**Version:** 1.0 – 2026‑04‑21  
**Author:** Aerospace Engineering Agent (AEA)  
**Audience:** Software Engineers, Product Managers, QA, Stakeholders

---

## 1. Introduction  

### 1.1 Purpose  
This document defines the functional and non‑functional requirements for an *Agentic AI System* that automatically generates detailed, actionable construction plans for a fixed‑wing Unmanned Aerial Vehicle (UAV) based on user‑defined constraints. The system will act as a virtual design engineer, providing sizing, performance estimation, propulsion & electronics selection, and structural recommendations.

### 1.2 Scope  
The system will:
- Accept user inputs for payload, airframe type, and propulsion type.
- Run four autonomous “agents” (Conceptual Design, Performance Estimation, Propulsion & Electronics, Structural Design).
- Produce a structured report in Markdown (or PDF) containing all design data and component recommendations.
- Operate as a web‑based service with a REST API and a lightweight UI for data entry and report download.

### 1.3 Definitions, Acronyms & Abbreviations  
| Term | Definition |
|------|------------|
| **UAV** | Unmanned Aerial Vehicle |
| **MTOW** | Maximum Take‑Off Weight |
| **CG** | Center of Gravity |
| **MAC** | Mean Aerodynamic Chord |
| **kV** | Motor RPM per Volt |
| **ESC** | Electronic Speed Controller |
| **Balsa** | Lightweight wood used in model aircraft |
| **Foam** | Expanded polystyrene or polyurethane foam |
| **Carbon Fiber** | Composite material for high strength-to-weight ratio |
| **V‑Tail** | Tail configuration with two surfaces forming a V |
| **High‑Wing** | Wing positioned above the fuselage |
| **Conventional** | Standard tail (horizontal + vertical) |
| **Flying Wing** | Wing‑only configuration with no distinct fuselage |

---

## 2. Overall Description  

### 2.1 Product Perspective  
The UAV Design Assistant is a standalone micro‑service that can be integrated into existing design pipelines or used as a standalone web application. It will rely on a rule‑based engine and lightweight physics models (e.g., lift‑drag equations, thrust‑to‑weight calculations) to produce design parameters. The system will be modular, allowing future expansion to other aircraft types (rotorcraft, VTOL, etc.).

### 2.2 User Characteristics  
- **Design Engineers** – require accurate sizing and component lists.  
- **Hobbyists** – need simplified, ready‑to‑build plans.  
- **Manufacturers** – require detailed material and structural data for production.  

### 2.3 Constraints  
- **Payload**: 0.5 kg – 10 kg (user‑defined).  
- **Airframe Types**: Conventional, Flying Wing, V‑Tail, High‑Wing.  
- **Propulsion**: Electric (LiPo) or Gas (piston).  
- **Regulatory**: Must comply with FAR 103 (if applicable) or user‑specified regulations.  
- **Performance**: Minimum stall speed ≤ 15 m/s for safety.  

### 2.4 Assumptions & Dependencies  
- Users provide accurate payload and desired flight envelope.  
- The system has access to a curated database of motors, ESCs, propellers, batteries, and avionics.  
- All calculations use standard atmospheric conditions (ISA).  
- The system is deployed on a server with Python 3.10+ and a lightweight web framework (FastAPI/Flask).  

---

## 3. Functional Requirements  

| FR‑ID | Description | Priority | Acceptance Criteria |
|-------|-------------|----------|----------------------|
| **FR‑1** | **Input Module** – Accept user inputs: payload weight, airframe type, propulsion type, optional constraints (e.g., max wingspan). | High | UI form validates numeric ranges; API accepts JSON payload. |
| **FR‑2** | **Agent 1 – Conceptual Design & Sizing** – Compute wingspan, wing area, chord, fuselage length, tail volume coefficient. | High | Output values satisfy aerodynamic stability criteria (e.g., tail volume > 0.5 for conventional). |
| **FR‑3** | **Agent 2 – Performance Estimation** – Estimate MTOW, stall speed, cruise speed, thrust‑to‑weight ratio. | High | Stall speed ≤ user‑specified max; MTOW within 10 % of calculated weight. |
| **FR‑4** | **Agent 3 – Propulsion & Electronics Selection** – Recommend motor (kV), ESC, propeller, battery, radio system. | High | Selected motor’s thrust ≥ 1.5 × MTOW; ESC rating ≥ 1.2× motor current; battery capacity ≥ 1.5× flight time target. |
| **FR‑5** | **Agent 4 – Structural Design & Material** – Suggest materials, spar placement, rib design, CG range. | Medium | Structural load calculations show safety factor ≥ 2.0 for all critical members. |
| **FR‑6** | **Report Generation** – Produce a Markdown report with sections: Design Overview, Dimensions, Propulsion System, Avionics, Construction Details. | High | Report includes all required tables and figures; downloadable as PDF. |
| **FR‑7** | **API Endpoints** – `/design` (POST) returns JSON and Markdown. | High | 200 OK with report; 400 Bad Request for invalid inputs. |
| **FR‑8** | **User Interface** – Web form for input, preview of report, download button. | Medium | Responsive design; accessible (WCAG 2.1 AA). |
| **FR‑9** | **Database Integration** – Store component catalogs, user history. | Medium | CRUD operations for component data. |
| **FR‑10** | **Logging & Audit** – Record design requests and outputs. | Low | Logs include timestamp, user ID, input parameters. |

---

## 4. Non‑Functional Requirements  

| NFR‑ID | Description | Priority | Acceptance Criteria |
|--------|-------------|----------|----------------------|
| **NFR‑1** | **Performance** – Generate report within 5 s for typical payloads. | High | End‑to‑end latency < 5 s. |
| **NFR‑2** | **Scalability** – Support up to 100 concurrent design requests. | Medium | Horizontal scaling via container orchestration. |
| **NFR‑3** | **Reliability** – 99.9 % uptime. | High | SLA with monitoring. |
| **NFR‑4** | **Security** – Input sanitization, HTTPS, JWT authentication for API. | High | No injection vulnerabilities; 256‑bit encryption. |
| **NFR‑5** | **Maintainability** | Medium | Codebase follows PEP‑8, uses unit tests (≥80 % coverage). |
| **NFR‑6** | **Portability** – Deployable on Linux, Windows, macOS. | Low | Docker image available. |
| **NFR‑7** | **Usability** – UI must be intuitive for non‑experts. | Medium | User testing score ≥ 4/5. |

---

## 5. System Features  

### 5.1 Input Validation & Constraints  
- Payload weight: 0.5 kg ≤ W ≤ 10 kg.  
- Airframe type: enum {Conventional, FlyingWing, VTail, HighWing}.  
- Propulsion type: enum {Electric, Gas}.  

### 5.2 Conceptual Design Calculations  
- **Wing loading**: \( W_{wing} = \frac{MTOW}{WingArea} \).  
- **Aspect ratio**: \( AR = \frac{Wingspan^2}{WingArea} \).  
- **Tail volume coefficient**: \( V_t = \frac{S_t \cdot l_t}{S_w \cdot c_{bar}} \).  

### 5.3 Performance Estimation  
- **Stall speed**: \( V_s = \sqrt{ \frac{2 \cdot MTOW}{\rho \cdot S_w \cdot C_{L_{max}}} } \).  
- **Cruise speed**: \( V_c = 1.3 \cdot V_s \).  
- **Thrust‑to‑weight**: \( \frac{T}{W} \geq 0.3 \) for electric, 0.4 for gas.  

### 5.4 Propulsion & Electronics Selection  
- **Motor**: kV chosen to achieve desired cruise speed with selected propeller.  
- **ESC**: Rated > 1.2× peak motor current.  
- **Battery**: LiPo cells (3.7 V each) in series/parallel to meet voltage & capacity.  
- **Radio**: 2.4 GHz, 8‑channel, telemetry (e.g., 3DR, FrSky).  

### 5.5 Structural Design  
- **Material**: Balsa core for low‑cost builds; Carbon Fiber for high‑strength.  
- **Spar**: Single‑box or double‑box depending on wing loading.  
- **Ribs**: Foam or balsa, spaced 10–15 cm.  
- **CG**: 25–35 % of mean aerodynamic chord (MAC).  

---

## 6. Use Cases  

| UC‑ID | Title | Actor | Description |
|-------|-------|-------|-------------|
| **UC‑1** | Generate UAV Design | Designer | Inputs parameters → system returns report. |
| **UC‑2** | View Component Catalog | User | Browse motors, ESCs, batteries. |
| **UC‑3** | Save & Retrieve Past Designs | User | Store design in database; retrieve later. |
| **UC‑4** | Export Report | User | Download Markdown or PDF. |

---

## 7. Data Requirements  

| Data Element | Type | Source | Notes |
|--------------|------|--------|-------|
| PayloadWeight | float | User | kg |
| AirframeType | enum | User | |
| PropulsionType | enum | User | |
| MTOW | float | Calculated | kg |
| WingArea | float | Calculated | m² |
| Wingspan | float | Calculated | m |
| FuselageLength | float | Calculated | m |
| MAC | float | Calculated | m |
| TailVolume | float | Calculated | dimensionless |
| StallSpeed | float | Calculated | m/s |
| CruiseSpeed | float | Calculated | m/s |
| MotorModel | string | Catalog | |
| ESCModel | string | Catalog | |
| PropellerSize | string | Catalog | |
| BatterySpecs | string | Catalog | |
| Avionics | string | Catalog | |

---

## 8. System Architecture  

```
+----------------+          +-------------------+          +-----------------+
|  Web UI / API  | <------> |  Design Engine    | <------> |  Component DB   |
+----------------+          +-------------------+          +-----------------+
          |                            |                            |
          | 1. User Input              | 2. Agent 1-4 Calculations  | 3. Component Lookup
          |                            |                            |
          |                            |                            |
          |                            |                            |
          +----------------------------+----------------------------+
                                   |
                               Report Generator
                                   |
                               Markdown / PDF
```

- **Design Engine**: Python modules implementing each agent.  
- **Component DB**: SQLite/PostgreSQL with tables for motors, ESCs, props, batteries, avionics.  
- **Report Generator**: Jinja2 templates → Markdown → PDF via wkhtmltopdf.

---

## 9. Acceptance Criteria  

1. **Accuracy** – All computed values must match analytical results within ±5 %.  
2. **Completeness** – Report must contain all sections listed in Output Requirements.  
3. **Usability** – UI must allow a novice to generate a design in < 2 min.  
4. **Performance** – API response < 5 s for payload ≤ 5 kg.  
5. **Security** – No exposed API keys; all data encrypted in transit.  

---

## 10. Appendices  

### 10.1 Component Catalog Sample  

| Motor | kV | Max Current (A) | Weight (g) |
|-------|----|-----------------|------------|
| EMAX MT2204 | 9200 | 30 | 30 |
| EMAX MT2213 | 9200 | 35 | 35 |

### 10.2 Glossary  

- **Aspect Ratio (AR)** – ratio of wingspan squared to wing area.  
- **C_Lmax** – maximum lift coefficient (assumed 1.5 for typical airfoils).  

### 10.3 References  

1. Anderson, J.D., *Introduction to Flight*, 5th ed., McGraw‑Hill, 2018.  
2. FAA FAR 103, *Ultralight Vehicles*.  
3. DJI, *Propeller and Motor Selection Guide*, 2023.  

---  

**End of SRS**