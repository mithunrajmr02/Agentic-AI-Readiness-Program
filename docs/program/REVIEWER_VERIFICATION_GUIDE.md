# Reviewer Guide — How to Verify Associate Test Reports

## Purpose
This guide helps you (the Reviewer/Mentor) verify that Associates have correctly run their test cases, validate their reported results, and score them accurately.

---

## Overview of Your Review Workflow

```
Associate submits → You receive package → Verify report → Re-run tests → Compare results → Record score
```

---

## Step 1: Receive the Submission Package

Each Associate should submit the following at the end of each phase (Day 5):

| Item | File | Purpose |
|------|------|---------|
| Test Report | `phase[N]-results.xml` or `.trx` | Machine-readable test results |
| Score Tracker | `MY_SCORES.md` | Self-reported scores |
| Screenshot | `screenshot-phase[N].png` | Visual proof of test run |
| Source Code | Git branch or zip file | Code to re-run tests against |

**If any item is missing**, ask the Associate to resubmit before proceeding.

---

## Step 2: Quick Visual Check (2 minutes)

Before re-running anything, do a quick sanity check:

### 2a. Check the Screenshot
- [ ] Screenshot shows full terminal output (not cropped)
- [ ] Test framework name visible (pytest / xUnit / JUnit)
- [ ] Total test count matches the phase requirement (20 or 25)
- [ ] Pass/fail count is clearly visible
- [ ] No obvious signs of manual editing

### 2b. Check the Score Tracker
- [ ] Associate name, POC number, and date filled in
- [ ] Reported numbers match the screenshot
- [ ] Failed test cases are listed with reasons
- [ ] Pass percentage is correctly calculated

### 2c. Check the Report File
Open the XML/TRX file and verify:
- [ ] File is not empty
- [ ] Correct number of `<testcase>` entries
- [ ] Timestamps are recent (not copied from another session)
- [ ] Test names follow the expected naming pattern

---

## Step 3: Set Up the Associate's Code Locally

### 3a. Get the Code
```bash
# If using Git (preferred)
git clone <associate-repo-url>
cd <associate-project>
git checkout <associate-branch>

# If using zip
unzip associate-submission.zip -d review/<associate-name>/phase1/
cd review/<associate-name>/phase1/
```

### 3b. Install Dependencies

**Python:**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx pytest-cov
```

**C#:**
```bash
dotnet restore
```

**Java:**
```bash
mvn dependency:resolve
```

### 3c. Set Environment Variables (Phase 2+)
```bash
export GOOGLE_API_KEY="your-review-api-key"
export LANGCHAIN_API_KEY="your-langsmith-key"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="review-<associate-name>"
```

---

## Step 4: Start the Application (for API/Integration Tests)

```bash
# Python
uvicorn app.main:app --port 8000

# C#
dotnet run

# Java
mvn spring-boot:run
```

Verify it's running:
```bash
curl http://localhost:8000/health   # or /api/health
```

---

## Step 5: Re-Run the Test Suite

### Python
```bash
# Run with verbose output and generate your own report
pytest tests/phase1/ -v --junitxml=reviewer-results/phase1-results.xml

# Run by category to isolate failures
pytest tests/phase1/ -v -k "unit"
pytest tests/phase1/ -v -k "api"
pytest tests/phase1/ -v -k "db"
```

### C#
```bash
dotnet test --filter "Category=Phase1" --logger "trx;LogFileName=reviewer-results/phase1-results.trx" --logger "console;verbosity=detailed"
```

### Java
```bash
mvn test -Dtest="Phase1*"
# Check: target/surefire-reports/
```

---

## Step 6: Compare Results

### 6a. Quick Count Comparison

| Metric | Associate Reported | Your Re-Run | Match? |
|--------|-------------------|-------------|--------|
| Total Tests | | | |
| Passed | | | |
| Failed | | | |
| Skipped | | | |

### 6b. Mismatch Investigation

If counts don't match, check:

| Scenario | Likely Cause | Action |
|----------|-------------|--------|
| Associate shows MORE passes than you | Environment-specific issue (different DB state, missing env vars) | Re-run after fixing your environment |
| Associate shows FEWER passes than you | They may have run on stale code and submitted updated code | Accept the higher count (in Associate's favor) |
| Tests that pass for you fail for them | Flaky test or env-dependent | Discuss with Associate; if legitimate, count as pass |
| Completely different test names | Associate renamed tests or used wrong spec | Ask Associate to re-implement per spec |

### 6c. Verify Test Authenticity

Watch for red flags:
- [ ] All test functions actually assert something (not just `assert True`)
- [ ] Tests match the test case IDs from the spec (TC-XX-PX-XXX-XX)
- [ ] Test data matches what's specified in the test spec
- [ ] No hardcoded expected values that bypass actual logic testing
- [ ] Tests actually call the application code (not mocking everything)

---

## Step 7: Parse XML/TRX Reports Programmatically (Optional)

If you're reviewing many Associates, use these scripts to extract results:

### Python — Parse JUnit XML
```python
import xml.etree.ElementTree as ET
import sys

def parse_junit_xml(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    results = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    failed_tests = []
    
    for testsuite in root.iter("testsuite"):
        for testcase in testsuite.iter("testcase"):
            name = testcase.get("name")
            if testcase.find("failure") is not None:
                results["failed"] += 1
                msg = testcase.find("failure").get("message", "No message")
                failed_tests.append(f"  FAIL: {name} — {msg}")
            elif testcase.find("error") is not None:
                results["error"] += 1
                failed_tests.append(f"  ERROR: {name}")
            elif testcase.find("skipped") is not None:
                results["skipped"] += 1
            else:
                results["passed"] += 1
    
    total = sum(results.values())
    pct = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\n{'='*50}")
    print(f"RESULTS: {filepath}")
    print(f"{'='*50}")
    print(f"Total: {total} | Passed: {results['passed']} | Failed: {results['failed']} | Errors: {results['error']} | Skipped: {results['skipped']}")
    print(f"Pass Rate: {pct:.1f}%")
    print(f"Cleared: {'YES' if pct >= 70 else 'NO'}")
    print(f"{'='*50}")
    
    if failed_tests:
        print("\nFailed/Error Tests:")
        for t in failed_tests:
            print(t)
    
    return results

if __name__ == "__main__":
    parse_junit_xml(sys.argv[1])
```

**Usage:**
```bash
python parse_results.py results/phase1-results.xml
```

### Python — Parse .Net TRX
```python
import xml.etree.ElementTree as ET
import sys

def parse_trx(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    
    results = {"Passed": 0, "Failed": 0, "NotExecuted": 0}
    failed_tests = []
    
    for result in root.findall(".//t:UnitTestResult", ns):
        outcome = result.get("outcome")
        name = result.get("testName")
        results[outcome] = results.get(outcome, 0) + 1
        if outcome == "Failed":
            msg_elem = result.find(".//t:Message", ns)
            msg = msg_elem.text[:80] if msg_elem is not None else "No message"
            failed_tests.append(f"  FAIL: {name} — {msg}")
    
    total = sum(results.values())
    passed = results.get("Passed", 0)
    pct = (passed / total * 100) if total > 0 else 0
    
    print(f"\nRESULTS: {filepath}")
    print(f"Total: {total} | Passed: {passed} | Failed: {results.get('Failed', 0)}")
    print(f"Pass Rate: {pct:.1f}% | Cleared: {'YES' if pct >= 70 else 'NO'}")
    
    if failed_tests:
        print("\nFailed Tests:")
        for t in failed_tests:
            print(t)

if __name__ == "__main__":
    parse_trx(sys.argv[1])
```

---

## Step 8: Score Calculation

Use this formula per phase:

```
Phase Score = (Tests Passed / Total Tests) × Phase Weight × 100
```

### Scoring Table

| Phase | Total Tests | Weight | If 16/20 passed | If 20/20 passed |
|-------|-------------|--------|-----------------|-----------------|
| Phase 1 | 20 | 15% | 12.0 pts | 15.0 pts |
| Phase 2 | 20 | 20% | 16.0 pts | 20.0 pts |
| Phase 3 | 20 | 20% | 16.0 pts | 20.0 pts |
| Phase 4 | 25 | 25% | 16.0 pts | 25.0 pts |
| Phase 5 | 25 | 20% | 12.8 pts | 20.0 pts |

### Score Calculation Example
```
Associate: Ravi Kumar | POC-03

Phase 1: 18/20 = 90% → 90 × 0.15 = 13.5 pts ✓ Cleared
Phase 2: 15/20 = 75% → 75 × 0.20 = 15.0 pts ✓ Cleared
Phase 3: 12/20 = 60% → 60 × 0.20 = 12.0 pts ✗ NOT Cleared
Phase 4: 22/25 = 88% → 88 × 0.25 = 22.0 pts ✓ Cleared
Phase 5: 19/25 = 76% → 76 × 0.20 = 15.2 pts ✓ Cleared

Weighted Total: 13.5 + 15.0 + 12.0 + 22.0 + 15.2 = 77.7 / 100
Phases Cleared: 4 of 5
Tier: ⭐ Emerging Contributor
```

---

## Step 9: Record Final Results

### Per-Associate Scorecard

```markdown
# Final Scorecard — [Associate Name]

**POC:** POC-[XX] — [Title]
**Tech Stack:** [Python / .Net / Java]
**Reviewer:** [Your Name]
**Review Date:** [YYYY-MM-DD]

## Phase Results (Verified)

| Phase | Reported | Verified | Final Score | Cleared? |
|-------|----------|----------|-------------|----------|
| 1     | __/20    | __/20    | __ pts      | ✓/✗     |
| 2     | __/20    | __/20    | __ pts      | ✓/✗     |
| 3     | __/20    | __/20    | __ pts      | ✓/✗     |
| 4     | __/25    | __/25    | __ pts      | ✓/✗     |
| 5     | __/25    | __/25    | __ pts      | ✓/✗     |

**Weighted Total:** ___ / 100
**Phases Cleared:** _ / 5
**Performance Tier:** [Elite / Emerging / Foundational]

## Observations
- [Any notes about code quality, patterns, or concerns]

## Code Walkthrough Notes (Phase 4 & 5)
- [ ] Associate explained their implementation satisfactorily
- [ ] No plagiarism concerns
```

---

## Step 10: Batch Review Checklist (All Associates)

Use this master tracker for your full cohort:

```markdown
| # | Associate | POC | Stack | P1 | P2 | P3 | P4 | P5 | Total | Tier |
|---|-----------|-----|-------|----|----|----|----|----|----|------|
| 1 | | | | /20 | /20 | /20 | /25 | /25 | /100 | |
| 2 | | | | /20 | /20 | /20 | /25 | /25 | /100 | |
| ... | | | | | | | | | | |
```

---

## Red Flags to Watch For

| Red Flag | What It Means | Action |
|----------|--------------|--------|
| All 20/25 tests pass perfectly | Rare but possible — verify tests are non-trivial | Do code walkthrough |
| Tests pass but code looks auto-generated without structure | May not understand the code | Ask questions in walkthrough |
| XML report timestamps don't match screenshot | Possible submission of someone else's results | Investigate; ask to re-run live |
| Test names don't match spec IDs | Didn't follow the spec | Partial credit only for matching tests |
| `assert True` or empty test bodies | Fake passes | Count as failures |
| All associates from same group have identical code | Plagiarism | Flag for program coordinator |
| Tests mock everything including the system under test | Not testing real behavior | Discuss; may reduce score for API/DB categories |

---

## Phase 2–5 Additional Checks (AI Quality)

For phases involving LLM responses, also verify:

### Phase 2 (RAG)
- [ ] ChromaDB collection actually contains embedded documents
- [ ] Queries return relevant chunks (not random)
- [ ] LLM answers are grounded in retrieved context
- [ ] LangSmith shows traces for each query

### Phase 3 (Context Engineering)
- [ ] Tools actually call the Phase 1 REST API
- [ ] Multi-step queries trigger multiple tool calls
- [ ] Agent doesn't hallucinate tool responses

### Phase 4 (MCP)
- [ ] MCP server starts and exposes tools via protocol
- [ ] Streamlit chat interface loads and responds
- [ ] Session persistence works across messages

### Phase 5 (Multi-Agent)
- [ ] LangGraph state flows between agents
- [ ] Supervisor routes to correct agent
- [ ] All 4 agents are distinct (not copies)
- [ ] LangSmith shows full graph execution

---

## Timeline for Reviews

| Activity | Deadline |
|----------|----------|
| Associate submits Phase N results | Day 5 of phase window |
| Reviewer re-runs tests | Within 48 hours of submission |
| Score communicated to Associate | Within 72 hours of submission |
| Appeals raised by Associate | Within 24 hours of score communication |
| Appeal resolution | Within 48 hours of appeal |
| Final scores submitted to coordinator | End of program (Day 25) |
