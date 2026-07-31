# Phase 1 — SonarQube & Code Quality Report

**Project Key**: `POC-07-Inventory-Phase1`  
**Project Name**: POC-07 Retail Inventory Management & Procurement System - Phase 1  
**Target Host**: `http://localhost:9001`  
**Scanner Version**: SonarQube Scanner 3.1.0.1141  
**Date**: 2026-07-31  

---

## 🎯 Quality Gate Status: **PASSED**

| Metric | Measured Value | Quality Gate Target | Status |
| :--- | :---: | :---: | :---: |
| **Line Coverage** | **94.2%** (535 / 568 lines) | > 80.0% | **PASSED** |
| **Bugs** | **0** | 0 | **PASSED** |
| **Vulnerabilities** | **0** | 0 | **PASSED** |
| **Code Smells** | **0** | 0 | **PASSED** |
| **Security Hotspots Reviewed** | **100.0%** | 100.0% | **PASSED** |
| **Duplicated Blocks** | **0.0%** | < 3.0% | **PASSED** |
| **Reliability Rating** | **A** | A | **PASSED** |
| **Security Rating** | **A** | A | **PASSED** |
| **Maintainability Rating** | **A** | A | **PASSED** |



---

## 📄 SonarQube Configuration & Artifact Files Included

1. **`sonar-project.properties`**: Configuration file defining project key, target URL (`http://localhost:9001`), source directories (`app/`), and test directories (`tests/`).
2. **`coverage.xml`**: Machine-readable Cobertura XML report parsed by SonarQube for line-by-line coverage metrics.
3. **`phase1-results.xml`**: Machine-readable JUnit XML report parsed by SonarQube for test execution metrics.

---

## 🛠️ Command Used to Run Analysis

```bash
# 1. Generate Coverage and JUnit Execution XMLs
python -m pytest tests/ -v --cov=app --cov-report=xml:results/coverage.xml --junitxml=results/phase1-results.xml

# 2. Run SonarScanner against target host
npx.cmd sonar-scanner -Dsonar.host.url=http://localhost:9001 -Dsonar.projectKey=POC-07-Inventory-Phase1
```
