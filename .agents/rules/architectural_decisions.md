# Architectural & Design Decisions Log

This document records the core design decisions, guardrail rules, and evaluation strategies established for the **AI Interview Agent** project. All current and future AI agents working on this codebase MUST understand and adhere to these decisions.

---

## 1. RAGAS Evaluation Framework & Role

* **Purpose**: RAGAS (Retrieval Augmented Generation Assessment) is used as an automated, behind-the-scenes quality assurance auditor. It evaluates LLM output quality across **Faithfulness**, **Answer Relevancy**, **Context Precision**, and **Context Recall**.
* **Latency Management**: RAGAS evaluations MUST NOT block the real-time candidate chat loop. Live turns deliver immediate candidate responses while RAGAS runs inside **Asynchronous Background Tasks** (`InterviewService._async_eval_and_save`) or **Offline MLOps Benchmarks** (`backend/scripts/run_ragas_eval.py`).
* **Offline Resiliency**: `RagasEvaluator` in `app/eval/ragas_evaluator.py` maintains a heuristic fallback method (`_fallback_eval`) so the application functions even when external RAGAS API calls are offline or disabled (`ragas_eval_enabled = False`).

---

## 2. Dual-Context Evaluation Strategy & Fallback Hierarchy

When evaluating candidate answers and AI feedback quality, **grounding exclusively to the Resume is forbidden**. Grounding must evaluate against both Expectations (Job Description) and Evidence (Resume).

The context builder (`resolve_dual_evaluation_context` in `app/guardrails/rules.py`) MUST follow this strict 3-step strategy hierarchy:

```
Step 1: Primary Strategy ("dual_context")
        Retrieve BOTH Job Description Context (JD RAG) + Candidate Resume Context (Resume RAG).
        Dual Context = [JD Chunks] + [Resume Chunks]
        │
        ▼ (If Resume is missing/unindexed)
Step 2: Fallback 1 ("jd_fallback")
        Retrieve Job Description Context (JD RAG / JD Description).
        Context = [JD Chunks]
        │
        ▼ (If specific JD database record is also missing)
Step 3: Fallback 2 ("generic_jd_fallback")
        Use a Generic Job Description Requirement Anchor per topic.
        Context = [Generic JD Anchor Chunk]
```

* **Rationale**: The Job Description (JD) represents the primary requirement benchmark. Evaluating against the JD ensures questions and scoring remain relevant to job competencies, while the Resume verifies factual accuracy.

---

## 3. LangGraph Interview Agent Workflow & Reflection

* **State Machine Flow**:
  `Planner` ➔ `Interviewer` ➔ `Wait For Candidate Answer` ➔ `Evaluator Node` ➔ `Reflection Node (Conditional)` ➔ `Report Generation`.
* **Reflection Guardrail**:
  If RAGAS Faithfulness score falls below the threshold ($\ge 0.75$), the graph routes to `reflection_node` to re-calibrate feedback. Reflection loops are strictly capped at a maximum of **2 iterations** (`reflection_count < 2`) to prevent infinite execution loops.

---

## 4. Multi-Layer Guardrails System

The codebase enforces 5 modular guardrails in `app/guardrails/rules.py`:

1. **Guardrail 1 (SQL Query Safety)**: Enforces read-only `SELECT` queries with automatic `LIMIT 50` clause insertion (`validate_sql_query_guardrail`).
2. **Guardrail 2 (PII Redaction)**: Redacts sensitive fields (`password_hash`, `ssn`, tokens) from DB outputs (`sanitize_db_result_guardrail`).
3. **Guardrail 3 (Question Safety)**: Blocks restricted/discriminatory topics (age, marital status, religion) in interview questions (`validate_interview_question_guardrail`).
4. **Guardrail 4 (Candidate Answer Safety)**: Detects prompt injections, jailbreaks, and self-harm keywords (`validate_candidate_answer_guardrail`).
5. **Guardrail 5 (RAGAS Dual-Context Guardrail)**: Validates evaluation feedback against Dual Context (JD + Resume) (`validate_evaluation_faithfulness_guardrail` & `resolve_dual_evaluation_context`).

---

## 5. Model Provider Standards

* **Default LLM Provider**: Google Gemini API via LiteLLM (`app/llm/gateway.py`).
* **Active Model Version**: `gemini/gemini-3.6-flash` (updated from legacy `gemini-2.0-flash` / `gemini-2.5-flash`).
* **Fallback Gateway**: If LLM API calls fail or keys are unconfigured, `LLMGateway` returns fallback structured mock responses to ensure robust UI demos.
