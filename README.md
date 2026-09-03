# IntelliVault
> **Secure Cloud Storage with AI-Powered Document Intelligence**

[![Phase](https://img.shields.io/badge/Phase-0%20Foundation%20(Complete)-teal.svg)](#development-phases)
[![Architecture](https://img.shields.io/badge/Stack-React%20%7C%20Flask%20%7C%20MongoDB%20%7C%20MinIO-0f766e.svg)](#technology-stack)
[![Security](https://img.shields.io/badge/Crypto-AES--256--GCM-emerald.svg)](#security--cryptography)
[![Documentation](https://img.shields.io/badge/Docs-55%20Sections%20(MD%20%26%20PDF)-blue.svg)](System/IntelliVault_Documentation.md)

---

## Overview

**IntelliVault** is a modern, security-first cloud file storage and document intelligence system. It combines client-transparent **zero-knowledge AES-256 GCM encryption** with self-hosted, explainable machine learning and computer vision pipelines (MobileNetV2, TF-IDF + LinearSVC, spaCy NER, and Isolation Forests).

Crucially, **no third-party generative AI APIs** are used for core intelligence features. All classification, auto-tagging, duplicate detection, PII redaction, and anomaly scoring execute locally within the controlled infrastructure.

---

## Technology Stack

* **Frontend:** React, Vite, Tailwind CSS, Lucide React, Axios
* **Backend:** Python, Flask (Application Factory, Blueprints), Flask-CORS
* **Persistence:** MongoDB (Metadata, directory trees, audit logs, ML tags)
* **Object Storage:** MinIO (Local development) / AWS S3 (Production deployment)
* **Security & Auth:** PyJWT, bcrypt, AES-256 GCM (Python `cryptography`)
* **AI & Machine Learning:** scikit-learn, NumPy, Pandas, MobileNetV2 / Keras, OpenCV, spaCy

---

## Development Phases

* [x] **Phase 0 ~ Foundation:** Architecture, Flask REST API factory, React Vite SPA, MongoDB & MinIO adapters, logging, 55-section master documentation & PDF compiler.
* [ ] **Phase 1 ~ Secure Cloud Storage:** JWT authentication, bcrypt passwords, file CRUD, folder hierarchy, versioning, AES-256 encryption, sharing tokens, audit logs.
* [ ] **Phase 2 ~ AI-Powered Document Intelligence:** MobileNetV2 image tagging, Grad-CAM explainability, TF-IDF document classification, pHash duplicate detection, spaCy PII redaction.
* [ ] **Phase 3 ~ Intelligent Security & Storage Optimization:** Access telemetry feature extraction, Isolation Forest anomaly scoring, Random Forest storage-tier prediction, retention policies.

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git

### 2. Setup Environment
```bash
# Clone repository
git clone https://github.com/vaibhavv1821/IntelliVault-Secure-Cloud-Storage-with-AI-Powered-Document-Intelligence.git
cd IntelliVault

# Copy environment template
cp .env.example .env
```

### 3. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run backend tests
python -m pytest backend/tests/

# Start Flask backend server (port 5000)
python backend/run.py
```

### 4. Frontend Setup
```bash
# Install npm dependencies
cd frontend
npm install

# Start Vite development server (port 5173)
npm run dev
```

### 5. Generate Technical Documentation PDF
```bash
python System/generate_pdf.py
```
This automatically parses `System/IntelliVault_Documentation.md` and compiles `System/IntelliVault_Documentation.pdf`.

---

## Master Documentation

All technical architectural choices, database schemas, cryptographic flows, ML evaluation criteria, engineering decisions, and interview preparation questions are maintained continuously in:
* **Markdown:** [`System/IntelliVault_Documentation.md`](System/IntelliVault_Documentation.md)
* **Compiled PDF:** [`System/IntelliVault_Documentation.pdf`](System/IntelliVault_Documentation.pdf)
