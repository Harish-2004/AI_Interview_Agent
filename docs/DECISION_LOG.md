# AI Interview Agent - Architectural Decision Record (ADR) Log

This document records the architectural decisions, design rationale, and system standards adopted in the **AI Interview Agent** project.

---

## Decision Record 1: RAGAS Evaluation Framework Role & Asynchronous Execution

* **Date**: August 31, 2026
* **Status**: Accepted
* **Context**: We needed an automated evaluation framework to measure RAG and LLM feedback quality across Faithfulness, Answer Relevancy, Context Precision, and Context Recall without manual human annotations.
* **Decision**: Integrated RAGAS (`app/eval/ragas_evaluator.py`). To protect user-facing chat latency (sub-second turns), RAGAS evaluation is offloaded to asynchronous background tasks (`InterviewService._async_eval_and_save`) and offline MLOps scripts (`scripts/run_ragas_eval.py`). A heuristic fallback (`_fallback_eval`) ensures the application functions even when external API keys are unavailable.

---

## Decision Record 2: Dual-Context Evaluation Strategy & Fallback Hierarchy

* **Date**: August 31, 2026
* **Status**: Accepted
* **Context**: Evaluating candidate responses solely against their resume causes two major issues: (1) it fails to measure job fit against hiring expectations, and (2) it risks asking questions irrelevant to the Job Description (JD).
* **Decision**: Implemented **Dual-Context Evaluation** in `resolve_dual_evaluation_context` (`app/guardrails/rules.py`):
  1. **Primary Strategy (`dual_context`)**: Ground against **BOTH** Job Description (JD = Requirement Anchor) and Candidate Resume (Resume = Evidence Anchor).
  2. **Fallback 1 (`jd_fallback`)**: If candidate resume RAG context is missing/unindexed, fall back to Job Description context.
  3. **Fallback 2 (`generic_jd_fallback`)**: If specific JD record is missing from the database, fall back to a generic JD requirement anchor per topic.

---

## Decision Record 3: LangGraph Agentic Interview State Machine & Reflection Loop

* **Date**: August 31, 2026
* **Status**: Accepted
* **Context**: Needed a multi-agent orchestration framework capable of planning skills, asking questions, evaluating candidate responses, and reflecting when low-faithfulness feedback is generated.
* **Decision**: Built a LangGraph state machine (`app/graphs/interview_graph.py`). If RAGAS Faithfulness falls below `0.75`, the graph routes to `reflection_node` to correct feedback. Reflection loops are capped at a maximum of **2 iterations** to prevent infinite execution loops.

---

## Decision Record 4: Modular Guardrail System

* **Date**: August 31, 2026
* **Status**: Accepted
* **Context**: Enterprise HR-Tech platforms require strict safety against SQL injection, PII leaks, discriminatory interview topics, prompt overrides, and hallucinated evaluations.
* **Decision**: Implemented 5 modular guardrails in `app/guardrails/rules.py`:
  - **Guardrail 1**: SQL Read-Only Enforcement (`validate_sql_query_guardrail`)
  - **Guardrail 2**: PII Redaction (`sanitize_db_result_guardrail`)
  - **Guardrail 3**: Discriminatory Question Blocking (`validate_interview_question_guardrail`)
  - **Guardrail 4**: Candidate Prompt Injection & Self-Harm Scanning (`validate_candidate_answer_guardrail`)
  - **Guardrail 5**: RAGAS Dual-Context Guardrail (`validate_evaluation_faithfulness_guardrail` & `resolve_dual_evaluation_context`)

---

## Decision Record 5: Active Gemini Model Provider Standard

* **Date**: August 31, 2026
* **Status**: Accepted
* **Context**: Legacy Gemini models (`gemini-2.0-flash`, `gemini-2.5-flash`) were deprecated by Google Cloud API.
* **Decision**: Updated system configuration (`app/config.py` and `.env`) to standard `gemini/gemini-3.6-flash`.
