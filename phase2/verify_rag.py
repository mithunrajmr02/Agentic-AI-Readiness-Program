import sys
import os
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from phase2.rag.rag_chain import build_rag_chain, ask_question

def verify_rag():
    print("=== Step 5 Verification: Real RAG Retrieval Queries ===")
    chain = build_rag_chain()

    test_queries = [
        "What is the reorder point formula?",
        "How is inventory valued using FIFO?",
        "When does a PO need Store Manager approval?",
        "What are the responsibilities of Anita Singh?",
        "What is the SKU format for grocery products?",
        "What are the stock movement types?",
        "How are active suppliers managed?",
        "What reports does the store manager review?"
    ]

    for q in test_queries:
        res = ask_question(q, chain)
        ans = res.get("answer", "")
        docs = res.get("source_documents", [])
        print(f"Q: {q}")
        print(f"A: {ans}")
        print(f"Docs returned: {len(docs)}\n")
        assert len(ans) > 0, f"Empty answer for '{q}'"

    print("=== Testing Out-of-Scope Query ===")
    oos_q = "Who won the Cricket World Cup?"
    oos_res = ask_question(oos_q, chain)
    oos_ans = oos_res.get("answer", "")
    print(f"Out-of-scope Q: {oos_q}")
    print(f"Out-of-scope A: {oos_ans}")
    assert "don't have that information in the inventory manual" in oos_ans.lower() or "don't have" in oos_ans.lower(), f"Unexpected out of scope answer: {oos_ans}"
    print("STEP 5 (RAG RETRIEVAL & OUT-OF-SCOPE) PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    verify_rag()
