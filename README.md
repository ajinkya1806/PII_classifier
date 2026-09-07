# PII / Sensitive Data Classification System

Enterprise-grade data classification API + SPA for **DPDP Act 2023** and **RBI-DADP** compliance.

Scans MySQL databases, classifies each column through a multi-method detection ensemble
(rule engine + pattern engine + LLM fallback), and presents results with confidence scores,
regulation tags, and full audit trails.

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  React SPA  │────▶│  FastAPI Backend (localhost:8000)         │
│ (Vite+TW)   │     │                                          │
│ :5173       │     │  ┌────────┐ ┌─────────┐ ┌───────────┐   │
└─────────────┘     │  │  Rule  │ │ Pattern │ │ LLM       │   │
                    │  │ Engine │ │ Engine  │ │ (Llama3.1)│   │
                    │  └───┬────┘ └────┬────┘ └─────┬─────┘   │
                    │      └──────┬────┘            │         │
                    │        ┌────▼────┐      ┌─────▼─────┐   │
                    │        │ Scorer  │◀─────│  Ollama   │   │
                    │        │+Categ.  │      │ :11434    │   │
                    │        └────┬────┘      └───────────┘   │
                    │        ┌────▼────┐                      │
                    │        │ SQLite  │  ◀── Jobs & Results   │
                    │        └────┬────┘                      │
                    │        ┌────▼────┐                      │
                    │        │ MySQL   │  ◀── Data Source      │
                    │        │Connector│                      │
                    │        └─────────┘                      │
                    └──────────────────────────────────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MySQL** (local instance)
- **Ollama** (optional, for LLM fallback)

## Quick Start

### 1. Install Ollama + Llama 3.1 (optional)

```bash
# Install Ollama — https://ollama.com/download
# Then pull the model:
ollama pull llama3.1
# Start Ollama (runs on localhost:11434):
ollama serve
```

### 2. Set Up MySQL Test Database

Create a test database with sample data covering multiple taxonomy subtypes:

```sql
CREATE DATABASE IF NOT EXISTS pii_test_db;
USE pii_test_db;

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    email_address VARCHAR(150),
    phone_number VARCHAR(15),
    aadhaar_number VARCHAR(14),
    pan_card VARCHAR(10),
    date_of_birth DATE,
    gender VARCHAR(10),
    postal_address TEXT,
    pincode VARCHAR(6)
);

INSERT INTO customers (full_name, email_address, phone_number, aadhaar_number, pan_card, date_of_birth, gender, postal_address, pincode) VALUES
('Rajesh Kumar', 'rajesh.kumar@example.com', '9876543210', '234567890123', 'ABCPD1234E', '1990-05-15', 'Male', '123 MG Road, Pune, Maharashtra', '411001'),
('Priya Sharma', 'priya.sharma@example.com', '8765432109', '345678901234', 'XYZPH5678K', '1985-11-20', 'Female', '456 Brigade Road, Bangalore, Karnataka', '560001'),
('Amit Patel', 'amit.p@example.com', '7654321098', '456789012345', 'DEFCL9012M', '1992-03-10', 'Male', '789 Park Street, Kolkata, West Bengal', '700001');

CREATE TABLE bank_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    bank_account_no VARCHAR(18),
    ifsc_code VARCHAR(11),
    upi_vpa VARCHAR(50),
    credit_card_number VARCHAR(19),
    cvv VARCHAR(4),
    card_expiry VARCHAR(7),
    loan_account_no VARCHAR(20),
    cibil_score INT,
    net_worth DECIMAL(15,2)
);

INSERT INTO bank_accounts (customer_id, bank_account_no, ifsc_code, upi_vpa, credit_card_number, cvv, card_expiry, loan_account_no, cibil_score, net_worth) VALUES
(1, '123456789012345', 'SBIN0001234', 'rajesh@upi', '4111111111111111', '123', '12/2025', 'LN0001234567', 750, 5000000.00),
(2, '987654321098765', 'HDFC0000001', 'priya@okicici', '5500000000000004', '456', '06/2026', 'LN0009876543', 800, 8500000.00),
(3, '456789012345678', 'ICIC0000002', 'amit@paytm', '378282246310005', '789', '03/2027', 'LN0004567890', 680, 3200000.00);

CREATE TABLE employee_sensitive (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(10),
    passport_number VARCHAR(8),
    voter_id VARCHAR(10),
    driving_license VARCHAR(16),
    religion VARCHAR(30),
    caste VARCHAR(30),
    disability_status VARCHAR(50),
    ip_address VARCHAR(45),
    password_hash VARCHAR(255),
    api_key VARCHAR(64)
);

INSERT INTO employee_sensitive (employee_id, passport_number, voter_id, driving_license, religion, caste, disability_status, ip_address, password_hash, api_key) VALUES
('EMP001', 'A1234567', 'ABC1234567', 'MH0120210012345', 'Hindu', 'General', 'None', '192.168.1.100', '$2b$12$abcdefghijklmnop', 'sk-abcdef1234567890abcdef1234567890'),
('EMP002', 'B2345678', 'DEF2345678', 'KA0220210023456', 'Muslim', 'OBC', 'Visual impairment', '10.0.0.50', '$2b$12$qrstuvwxyz123456', 'sk-ghijkl1234567890ghijkl1234567890'),
('EMP003', 'C3456789', 'GHI3456789', 'DL0320210034567', 'Christian', 'SC', 'None', '172.16.0.25', '$2b$12$mnopqrstuvwxyz78', 'sk-mnopqr1234567890mnopqr1234567890');

CREATE TABLE health_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100),
    medical_diagnosis TEXT,
    prescription_data TEXT,
    health_insurance_id VARCHAR(20),
    fingerprint_ref VARCHAR(64),
    abha_id VARCHAR(14)
);

INSERT INTO health_records (patient_name, medical_diagnosis, prescription_data, health_insurance_id, fingerprint_ref, abha_id) VALUES
('Rajesh Kumar', 'Type 2 Diabetes', 'Metformin 500mg twice daily', 'HI001234567890', 'fp_hash_abc123', '12345678901234'),
('Priya Sharma', 'Hypertension', 'Amlodipine 5mg once daily', 'HI002345678901', 'fp_hash_def456', '23456789012345'),
('Amit Patel', 'Asthma', 'Salbutamol inhaler as needed', 'HI003456789012', 'fp_hash_ghi789', '34567890123456');
```

### 3. Run the Backend

```bash
cd g:\PII_classifier

# Install Python dependencies
pip install -r requirements.txt

# Start the API server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 4. Run the Frontend

```bash
cd g:\PII_classifier\frontend

# Install Node dependencies (if not already done)
npm install

# Start the dev server
npm run dev
```

The SPA will be available at `http://localhost:5173`.

## End-to-End Walkthrough

1. Open `http://localhost:5173` in your browser
2. Enter your MySQL connection details (host, port, user, password, database)
3. Click **"Test Connection"** to verify connectivity
4. Click **"Connect & Browse"** to load the schema
5. In the Schema Browser, select tables to scan (all selected by default)
6. Click **"Run Scan"** to start the classification
7. Watch the live progress bar as fields are analyzed
8. View color-coded results:
   - 🔴 Red = Financial Sensitive (RBI-DADP)
   - 🟠 Orange = Sensitive Personal Data (DPDP)
   - 🟡 Yellow = PII
   - ⚪ Gray = Non-Sensitive
9. Click any row to see engine breakdown in the detail drawer
10. Export results as JSON or CSV

## Configuration

### taxonomy.yaml

Add new subtypes without code changes:

```yaml
- name: "New Data Type"
  category: "PII"
  regulation: "DPDP"
  keywords: ["new_keyword", "another_keyword"]
  base_keyword_confidence: 0.60
  pattern_ref: null  # or a pattern engine validator key
```

### weights.yaml

Adjust engine weights (must sum to 1.0):

```yaml
engine_weights:
  rule_engine: 0.35
  pattern_engine: 0.45
  llm_engine: 0.20
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/connections/test` | Validate MySQL connection |
| POST | `/connections/schema` | List tables + columns |
| POST | `/scan` | Start async scan → `{job_id}` |
| GET | `/scan/{job_id}` | Job status + progress |
| GET | `/scan/{job_id}/results` | Classification results |
| GET | `/scan/{job_id}/export?format=json\|csv` | Export results |
| GET | `/scan/{job_id}/stream` | SSE live progress |
| GET | `/jobs` | List past scan jobs |
| GET | `/health` | Health check |

## Testing

```bash
cd g:\PII_classifier
python -m pytest tests/ -v
```

## Project Structure

```
pii_classifier/
├── api/main.py                 # FastAPI application
├── connectors/
│   ├── base.py                 # DataAsset, TableConnector, FileConnector ABCs
│   ├── registry.py             # Connector registry/factory
│   └── mysql_connector.py      # MySQL implementation
├── engines/
│   ├── rule_engine.py          # Keyword/name matching (taxonomy.yaml driven)
│   ├── pattern_engine.py       # Regex/checksum validators (21 validators)
│   └── llm_engine.py           # Llama 3.1 via Ollama (fallback)
├── classifier/
│   ├── scorer.py               # Weighted confidence combination
│   └── categorizer.py          # Score → DPDP/RBI-DADP classification
├── config/
│   ├── taxonomy.yaml           # Full 50+ subtype dictionary
│   └── weights.yaml            # Engine weights + thresholds
├── jobs/
│   ├── store.py                # SQLite persistence
│   └── runner.py               # Async scan execution
├── frontend/                   # React + Vite + TypeScript + Tailwind SPA
├── tests/                      # 51 unit tests
└── README.md
```
