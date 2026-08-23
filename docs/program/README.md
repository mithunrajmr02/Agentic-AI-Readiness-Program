# AI Readiness Training Program — POC Repository

## Program Overview

This repository contains the complete documentation, user stories, implementation guides, and test specifications for the **AI Readiness Training Program** — a structured 5-phase upskilling initiative for fresh joiners with backgrounds in Python, .Net C#, or Java Full Stack development.

**Program Goal:** Equip bench associates with practical AI engineering skills — from building full-stack applications with GitHub Copilot, to building RAG pipelines, context-aware agents, MCP servers, and multi-agent systems — making them deployment-ready for AI-focused project allocations.

---

## How to Use This Repository

1. **Pick one POC** from the table below that matches your domain interest
2. **Read the `overview.md`** in your chosen POC folder to understand the full scope
3. **Start Phase 1** by reading `phase1-fullstack-crud.md` — follow it step by step
4. **After completing each phase**, run the test suite in `tests/phase[N]-test-spec.md` and record your pass/fail counts
5. **Submit results** to your mentor at the end of each 5-day phase window
6. **Progress linearly** — each phase builds directly on the previous one

> **Important:** You implement the same POC across all 5 phases. Do NOT switch POCs mid-program.

---

## The 10 POCs

| # | Domain | POC Title | Folder | Description |
|---|--------|-----------|--------|-------------|
| POC-01 | Banking | Loan Application Management System | `banking/POC-01-Loan-Application-Management/` | Full lifecycle management of personal, home, and auto loan applications from submission to disbursement |
| POC-02 | Banking | Personal Finance Tracker & Analytics | `banking/POC-02-Personal-Finance-Tracker/` | Income/expense tracking, budget management, and AI-powered financial insights for individual users |
| POC-03 | Telecom | Customer Support Ticket Management | `telecom/POC-03-Customer-Support-Tickets/` | End-to-end support ticket lifecycle with prioritization, assignment, and resolution tracking |
| POC-04 | Telecom | Network Outage Reporting & Resolution | `telecom/POC-04-Network-Outage-Tracker/` | Real-time outage reporting, impact assessment, and resolution coordination across network regions |
| POC-05 | Energy | Smart Meter Data Management | `energy/POC-05-Smart-Meter-Analytics/` | Smart meter reading ingestion, consumption analytics, anomaly detection, and billing generation |
| POC-06 | Energy | Renewable Energy Asset Tracking | `energy/POC-06-Renewable-Asset-Tracking/` | Solar/wind asset performance monitoring, maintenance scheduling, and energy output reporting |
| POC-07 | Retail | Inventory Management & Procurement | `retail/POC-07-Inventory-Management/` | Product catalog, stock management, low-stock alerting, and supplier order management |
| POC-08 | Retail | Customer Loyalty Program Management | `retail/POC-08-Loyalty-Program/` | Points accumulation, redemption, tier management, and AI-driven promotion recommendations |
| POC-09 | Consumer | Recipe & Meal Planning Application | `consumer/POC-09-Recipe-Meal-Planner/` | Recipe catalog, weekly meal planning, nutrition tracking, and AI-powered dietary recommendations |
| POC-10 | Consumer | Travel Itinerary Planner & Expense Tracker | `consumer/POC-10-Travel-Itinerary-Planner/` | Trip planning, itinerary management, booking tracking, and AI-assisted budget optimization |

---

## Phase Overview

| Phase | Name | Duration | Score Weight | What You Build |
|-------|------|----------|-------------|----------------|
| **Phase 1** | Full Stack CRUD with Copilot | 5 days | 15% | End-to-end full stack app (REST API + React UI + SQLite) built via GitHub Copilot vibe coding |
| **Phase 2** | RAG Application | 5 days | 20% | LangChain RAG pipeline (ChromaDB + Gemini 2.0 Flash) that answers questions about your app's user manual |
| **Phase 3** | Context Engineering & Tool Integration | 5 days | 20% | Expand RAG to call your Phase 1 REST API as tools; ReAct agent with context-engineered prompts |
| **Phase 4** | MCP Server & Chat Interface | 5 days | 25% | Convert REST API to MCP server; build a Streamlit chat interface connected via LangChain |
| **Phase 5** | Multi-Agent with LangGraph | 5 days | 20% | LangGraph StateGraph with 4 specialized agents orchestrated by a Supervisor pattern |

**Total Program Duration:** ~25 working days (5 weeks)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend (choose one)** | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| | .Net 8 + ASP.NET Core Web API + Entity Framework Core |
| | Java 21 + Spring Boot 3 + Spring Data JPA |
| **Frontend (React mandatory + one more)** | React 18 + Vite + Axios |
| | Angular 17 / Blazor / Thymeleaf / Streamlit |
| **Database** | SQLite |
| **LLM** | Google Gemini 2.0 Flash (Google AI Studio free tier) |
| **Vector Database** | ChromaDB |
| **AI Orchestration (P2–P4)** | LangChain + langchain-google-genai |
| **AI Orchestration (P5)** | LangGraph |
| **MCP Framework (P4)** | fastmcp (Python) |
| **Observability** | LangSmith + structlog/Serilog/SLF4J + OpenTelemetry |
| **Testing** | pytest + httpx / xUnit / JUnit 5 |
| **Vibe Coding** | GitHub Copilot (pre-provisioned) |

---

## Scoring & Performance Tiers

### Phase Weights

| Phase | Weight | Max Score | Pass Threshold (70%) |
|-------|--------|-----------|----------------------|
| Phase 1 | 15% | 15 points | 10.5 points |
| Phase 2 | 20% | 20 points | 14 points |
| Phase 3 | 20% | 20 points | 14 points |
| Phase 4 | 25% | 25 points | 17.5 points |
| Phase 5 | 20% | 20 points | 14 points |
| **Total** | **100%** | **100 points** | **70 points** |

### Performance Tiers

| Tier | Criteria | Label |
|------|----------|-------|
| 🏆 **Elite Performer** | Cleared all 5 phases (≥70% in each) | Priority allocation to advanced AI projects |
| ⭐ **Emerging Contributor** | Cleared exactly 4 phases | Allocation to AI-adjacent projects with mentoring |
| 🌱 **Foundational Builder** | Cleared 3 or fewer phases | Assigned foundational AI tasks; extended learning plan |

> A phase is "cleared" when ≥70% of that phase's automated test cases pass.

---

## Repository Structure

```
d:/ICD_NGA_AI Readiness_Program_POCs/
├── README.md                          ← You are here
├── TECH_STACK_REFERENCE.md            ← Environment setup for all 3 stacks
├── SCORING_RUBRIC.md                  ← Test categories, weights, evaluation guide
├── OBSERVABILITY_GUIDE.md             ← LangSmith + OpenTelemetry setup guide
│
├── banking/
│   ├── POC-01-Loan-Application-Management/
│   │   ├── overview.md
│   │   ├── phase1-fullstack-crud.md
│   │   ├── phase2-rag-application.md
│   │   ├── phase3-context-engineering.md
│   │   ├── phase4-mcp-chat-interface.md
│   │   ├── phase5-multi-agent.md
│   │   └── tests/
│   │       ├── phase1-test-spec.md
│   │       ├── phase2-test-spec.md
│   │       ├── phase3-test-spec.md
│   │       ├── phase4-test-spec.md
│   │       └── phase5-test-spec.md
│   └── POC-02-Personal-Finance-Tracker/
│       └── [same structure]
│
├── telecom/
│   ├── POC-03-Customer-Support-Tickets/
│   └── POC-04-Network-Outage-Tracker/
│
├── energy/
│   ├── POC-05-Smart-Meter-Analytics/
│   └── POC-06-Renewable-Asset-Tracking/
│
├── retail/
│   ├── POC-07-Inventory-Management/
│   └── POC-08-Loyalty-Program/
│
└── consumer/
    ├── POC-09-Recipe-Meal-Planner/
    └── POC-10-Travel-Itinerary-Planner/
```

---

## Quick Start

### Step 1: Pick Your POC
Review the table above and choose one POC. Discuss with your mentor if unsure.

### Step 2: Set Up Your Environment
Read `TECH_STACK_REFERENCE.md` and complete the setup for your chosen stack (Python / .Net / Java). Set up Google AI Studio API key, LangSmith account, and GitHub Copilot.

### Step 3: Begin Phase 1
Open your chosen POC folder and read `overview.md`, then `phase1-fullstack-crud.md`. Follow the 5-day schedule and implementation guide.

### Step 4: Run Tests After Each Phase
After completing implementation, run the test suite from `tests/phase[N]-test-spec.md`. Record your pass/fail counts and submit to your mentor.

### Step 5: Progress to Next Phase
Each phase builds on the previous. Do not skip ahead — Phase 2 requires Phase 1's running application.

---

## Mentoring Schedule

| Day | Session | Duration |
|-----|---------|----------|
| Day 1 of each phase | Concept introduction + Q&A | 1 hour |
| Day 2–3 | Implementation check-in | 1 hour |
| Day 4 | Troubleshooting + code review | 1 hour |
| Day 5 | Test run + phase wrap-up | 1 hour |

> Mentor contact: _[To be filled by program coordinator]_
> Mentoring channel: _[To be filled by program coordinator]_

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `TECH_STACK_REFERENCE.md` | Step-by-step environment setup for Python, .Net, Java, Google AI Studio, LangSmith, ChromaDB, GitHub Copilot |
| `SCORING_RUBRIC.md` | Detailed scoring breakdown, test case categories, evaluation criteria, AI quality metrics |
| `OBSERVABILITY_GUIDE.md` | LangSmith tracing setup, OpenTelemetry span guide, structured logging standards for all 5 phases |
