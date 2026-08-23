# Associate Guide — How to Run Tests & Generate Reports

## Purpose
This guide helps you (the Associate) run the test cases for each phase, generate a structured test report, and submit it to your reviewer/mentor.

---

## Prerequisites (One-Time Setup)

### Python Stack
```bash
pip install pytest pytest-asyncio httpx pytest-cov
```

### .Net C# Stack
```bash
dotnet add package xunit
dotnet add package xunit.runner.visualstudio
dotnet add package Microsoft.NET.Test.Sdk
```

### Java Stack
```bash
# Ensure pom.xml has JUnit 5 + Maven Surefire plugin
mvn dependency:resolve
```

---

## Step-by-Step: Running Tests & Generating Reports

### Step 1: Navigate to Your Project Directory

```bash
cd your-project-folder/
```

Ensure your application is running (for API/integration tests):
```bash
# Python
uvicorn app.main:app --port 8000 &

# .Net
dotnet run &

# Java
mvn spring-boot:run &
```

---

### Step 2: Implement the Test Cases

Each phase has a test spec file at:
```
tests/phase[N]-test-spec.md
```

- Read the spec carefully — it provides **code skeletons** for each test
- Create your test files following the naming convention:
  - Python: `tests/phase1/test_unit.py`, `tests/phase1/test_api.py`, `tests/phase1/test_db.py`
  - C#: `Tests/Phase1/UnitTests.cs`, `Tests/Phase1/ApiTests.cs`, `Tests/Phase1/DbTests.cs`
  - Java: `src/test/java/com/yourapp/phase1/UnitTests.java`, etc.
- Copy the code skeleton from the spec and adapt it to your implementation
- Each test function should map 1:1 to a test case ID (e.g., `TC-01-P1-UNIT-01`)

---

### Step 3: Run Tests and Generate the Report File

#### Python (pytest) — Recommended Commands

```bash
# Run all Phase 1 tests with verbose output
pytest tests/phase1/ -v

# Generate XML report (REQUIRED for submission)
pytest tests/phase1/ --junitxml=results/phase1-results.xml -v

# Generate HTML coverage report (optional, bonus)
pytest tests/phase1/ -v --cov=app --cov-report=html --cov-report=term

# Run by category
pytest tests/phase1/ -v -k "unit"
pytest tests/phase1/ -v -k "api"
pytest tests/phase1/ -v -k "db"
```

#### .Net C# (xUnit) — Recommended Commands

```bash
# Run all Phase 1 tests with detailed output
dotnet test --filter "Category=Phase1" --logger "console;verbosity=detailed"

# Generate TRX report (REQUIRED for submission)
dotnet test --filter "Category=Phase1" --logger "trx;LogFileName=results/phase1-results.trx"

# Generate HTML report (optional)
dotnet test --filter "Category=Phase1" --logger "html;LogFileName=results/phase1-results.html"
```

#### Java (JUnit 5 + Maven) — Recommended Commands

```bash
# Run all Phase 1 tests
mvn test -Dtest="Phase1*"

# Generate Surefire XML report (REQUIRED for submission)
mvn test -Dtest="Phase1*"
# Reports auto-generated at: target/surefire-reports/

# Generate HTML report (optional)
mvn surefire-report:report
# HTML report at: target/site/surefire-report.html
```

---

### Step 4: Verify Your Results Locally

After running, check the console output. You'll see something like:

**Python:**
```
==================== test session starts ====================
tests/phase1/test_unit.py::test_create_applicant_valid PASSED
tests/phase1/test_unit.py::test_create_applicant_invalid_email PASSED
tests/phase1/test_unit.py::test_calculate_emi FAILED
...
==================== 16 passed, 4 failed ====================
```

**C#:**
```
Passed!  - Failed:  4, Passed: 16, Skipped: 0, Total: 20
```

**Java:**
```
Tests run: 20, Failures: 4, Errors: 0, Skipped: 0
```

Record your counts:
- Total tests: ___
- Passed: ___
- Failed: ___
- Pass percentage: ___

---

### Step 5: Fill the Score Tracker

Create a file called `MY_SCORES.md` in your project root:

```markdown
# Test Score Tracker

**Associate Name:** [Your Name]
**POC Number:** POC-[XX]
**Tech Stack:** [Python / .Net / Java]
**Date:** [YYYY-MM-DD]

## Phase Results

| Phase | Tests Passed | Total Tests | % Score | Cleared (≥70%)? |
|-------|-------------|-------------|---------|-----------------|
| 1     |             | 20          |         |                 |
| 2     |             | 20          |         |                 |
| 3     |             | 20          |         |                 |
| 4     |             | 25          |         |                 |
| 5     |             | 25          |         |                 |

**Weighted Total:** _____ / 100
**Performance Tier:** _______________

## Failed Test Cases (List each failed TC ID and reason)

| Test Case ID | Reason for Failure |
|--------------|-------------------|
| TC-XX-PX-XXX-XX | Brief description |
```

---

### Step 6: Take a Console Screenshot

- Take a screenshot of the terminal showing the full test run output
- Ensure the screenshot clearly shows:
  - Total test count
  - Pass/fail count
  - Individual test names with their PASSED/FAILED status

---

### Step 7: Prepare Submission Package

Create a folder structure for submission:

```
submission/
├── phase1-results.xml          ← Generated report file (XML/TRX)
├── MY_SCORES.md                ← Your score tracker
├── screenshot-phase1.png       ← Terminal screenshot
└── source-code/                ← Your complete project code
    ├── app/
    ├── tests/
    └── ...
```

---

### Step 8: Submit to Reviewer

Share the following with your reviewer/mentor:
1. **Report file** — `phase1-results.xml` (or `.trx` for .Net)
2. **Score tracker** — `MY_SCORES.md`
3. **Screenshot** — Terminal output screenshot
4. **Source code** — Push to assigned repo branch OR zip and share

**Submission deadline:** End of Day 5 of each phase window.

---

## Quick Reference — Commands Per Phase

| Phase | Python Command | Report Output |
|-------|---------------|---------------|
| Phase 1 | `pytest tests/phase1/ --junitxml=results/phase1-results.xml -v` | `results/phase1-results.xml` |
| Phase 2 | `pytest tests/phase2/ --junitxml=results/phase2-results.xml -v` | `results/phase2-results.xml` |
| Phase 3 | `pytest tests/phase3/ --junitxml=results/phase3-results.xml -v` | `results/phase3-results.xml` |
| Phase 4 | `pytest tests/phase4/ --junitxml=results/phase4-results.xml -v` | `results/phase4-results.xml` |
| Phase 5 | `pytest tests/phase5/ --junitxml=results/phase5-results.xml -v` | `results/phase5-results.xml` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -e .` from project root |
| API tests fail with connection error | Ensure your app server is running on the correct port |
| Database tests fail | Check SQLite file path; ensure test DB is separate from dev DB |
| LangSmith tests fail (Phase 2+) | Verify `LANGCHAIN_API_KEY` and `LANGCHAIN_TRACING_V2=true` are set |
| ChromaDB tests fail (Phase 2+) | Ensure ChromaDB is initialized and collection exists |
| MCP tests fail (Phase 4) | Ensure MCP server is running before executing tests |

---

## Important Notes

- You must implement ALL test cases listed in the spec, even if you think some won't pass
- Do NOT modify the test assertions to make them pass artificially
- If a test genuinely cannot pass due to a design difference, document it in the "Failed Test Cases" table with an explanation
- Your reviewer will re-run your tests against your code — results must be reproducible
