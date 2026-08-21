import os
import sys
import subprocess

repo_root = os.path.abspath(os.path.dirname(__file__))

def run_pytest(directory, name):
    print(f"\n{'='*60}")
    print(f"Running {name} Tests in: {directory}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, "-m", "pytest", directory,
        "-v"
    ]
    res = subprocess.run(cmd, cwd=repo_root)
    return res.returncode == 0

def main():
    print("Starting Unified Multi-Phase Verification Suite")
    
    phases = [
        ("phase1/tests/", "Phase 1 (FastAPI Backend)"),
        ("phase2/tests/", "Phase 2 (RAG & ChromaDB)"),
        ("phase3/tests/", "Phase 3 (LangChain ReAct Agent)")
    ]
    
    results = {}
    for directory, name in phases:
        if os.path.exists(os.path.join(repo_root, directory)):
            results[name] = run_pytest(directory, name)
        else:
            print(f"Warning: Directory {directory} not found. Skipping {name}.")
            results[name] = False
            
    print(f"\n{'='*60}")
    print("📊 Verification Summary")
    print(f"{'='*60}")
    all_passed = True
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{name.ljust(40)} {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\nAll phases passed successfully! The refactoring to src/ is working.")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
