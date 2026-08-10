# Phase 2 Automated Test Execution Report

**Project:** POC-07 — Inventory Management & Procurement System  
**Phase:** Phase 2 (RAG Application)  
**Execution Date:** 2026-08-10  
**Total Duration:** 5.60 seconds  
**Total Test Cases:** 33  
**Passed:** 33  
**Failed:** 0  
**Pass Rate:** 100.0%  

---

## Detailed Test Case Breakdown

| # | Test Name | Class / Module | Duration (s) | Status |
|---|-----------|----------------|--------------|--------|
| 1 | `test_manual_loads` | `phase2.tests.test_phase2` | 0.005s | **PASSED** |
| 2 | `test_chunks_size` | `phase2.tests.test_phase2` | 0.002s | **PASSED** |
| 3 | `test_min_chunks` | `phase2.tests.test_phase2` | 0.003s | **PASSED** |
| 4 | `test_chromadb_collection` | `phase2.tests.test_phase2` | 1.225s | **PASSED** |
| 5 | `test_sku_query` | `phase2.tests.test_phase2` | 0.126s | **PASSED** |
| 6 | `test_top_k` | `phase2.tests.test_phase2` | 0.011s | **PASSED** |
| 7 | `test_irrelevant_low_score` | `phase2.tests.test_phase2` | 0.002s | **PASSED** |
| 8 | `test_po_lifecycle` | `phase2.tests.test_phase2` | 0.021s | **PASSED** |
| 9 | `test_empty_query` | `phase2.tests.test_phase2` | 0.009s | **PASSED** |
| 10 | `test_latency` | `phase2.tests.test_phase2` | 0.017s | **PASSED** |
| 11 | `test_reorder_formula` | `phase2.tests.test_phase2` | 0.016s | **PASSED** |
| 12 | `test_po_approval` | `phase2.tests.test_phase2` | 0.014s | **PASSED** |
| 13 | `test_movement_types` | `phase2.tests.test_phase2` | 0.017s | **PASSED** |
| 14 | `test_out_of_scope` | `phase2.tests.test_phase2` | 0.017s | **PASSED** |
| 15 | `test_non_empty` | `phase2.tests.test_phase2` | 0.039s | **PASSED** |
| 16 | `test_category_management` | `phase2.tests.test_phase2` | 0.018s | **PASSED** |
| 17 | `test_langsmith` | `phase2.tests.test_phase2` | 0.020s | **PASSED** |
| 18 | `test_otel_spans` | `phase2.tests.test_phase2` | 0.024s | **PASSED** |
| 19 | `test_log_poc_id` | `phase2.tests.test_phase2` | 0.025s | **PASSED** |
| 20 | `test_sources` | `phase2.tests.test_phase2` | 0.019s | **PASSED** |
| 21 | `test_ingest_main` | `phase2.tests.test_phase2` | 0.331s | **PASSED** |
| 22 | `test_ingest_file_not_found` | `phase2.tests.test_phase2` | 0.002s | **PASSED** |
| 23 | `test_get_embeddings_branches` | `phase2.tests.test_phase2` | 2.043s | **PASSED** |
| 24 | `test_local_llm_all_topics` | `phase2.tests.test_phase2` | 0.021s | **PASSED** |
| 25 | `test_build_rag_chain_with_google_key` | `phase2.tests.test_phase2` | 0.136s | **PASSED** |
| 26 | `test_ingest_small_chunk_warning` | `phase2.tests.test_phase2` | 0.002s | **PASSED** |
| 27 | `test_ingest_build_vectorstore_default` | `phase2.tests.test_phase2` | 0.112s | **PASSED** |
| 28 | `test_vectorstore_alt_paths` | `phase2.tests.test_phase2` | 0.033s | **PASSED** |
| 29 | `test_ask_question_chain_none` | `phase2.tests.test_phase2` | 0.016s | **PASSED** |
| 30 | `test_ask_question_exception_handling` | `phase2.tests.test_phase2` | 0.005s | **PASSED** |
| 31 | `test_ingest_script_entrypoint` | `phase2.tests.test_phase2` | 0.089s | **PASSED** |
| 32 | `test_get_embeddings_exception` | `phase2.tests.test_phase2` | 0.064s | **PASSED** |
| 33 | `test_otel_exception_handling` | `phase2.tests.test_phase2` | 0.019s | **PASSED** |

---

## Summary Statement
All 33 test cases executed cleanly against the Phase 2 RAG pipeline implementation, satisfying all ingestion, retrieval, generation, and observability standards specified in `phase2-test-spec.md`.
