"""Modular Application Guardrail Rules.

This module defines hybrid guardrail checks combining:
1. Fast pattern scanning for critical safety violations (self-harm, violence, hate speech, SQL safety, PII).
2. Semantic intent evaluation to catch prompt injections, jailbreaks, and inappropriate topics.
"""

import re
from typing import Any
from app.eval.ragas_evaluator import ragas_evaluator


# =====================================================================
# 1. DATABASE & TOOL GUARDRAILS
# =====================================================================

def validate_sql_query_guardrail(query: str) -> dict[str, Any]:
    """Guardrail 1: Enforces read-only SELECT queries, blocks mutation keywords, and enforces result limits."""
    clean_query = query.strip().lower()

    if not (clean_query.startswith("select") or clean_query.startswith("pragma") or clean_query.startswith("explain")):
        return {
            "passed": False,
            "error": "Security Error: Only read-only SELECT queries are allowed.",
            "query": query,
        }

    forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create"]
    for keyword in forbidden_keywords:
        if f" {keyword} " in f" {clean_query} ":
            return {
                "passed": False,
                "error": f"Security Error: Forbidden keyword '{keyword}' detected.",
                "query": query,
            }

    # Automatically enforce a maximum row limit if not specified
    modified_query = query
    if "limit" not in clean_query:
        modified_query = f"{query.rstrip(';')} LIMIT 50;"

    return {
        "passed": True,
        "query": modified_query,
        "error": None,
    }


def sanitize_db_result_guardrail(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Guardrail 2: Sanitizes database rows by redacting sensitive PII columns."""
    sensitive_keys = {"password", "password_hash", "ssn", "secret", "token", "jwt", "private_key"}
    sanitized_data = []

    for row in data:
        cleaned_row = {}
        for key, value in row.items():
            if key.lower() in sensitive_keys:
                cleaned_row[key] = "[REDACTED_PII]"
            else:
                cleaned_row[key] = value
        sanitized_data.append(cleaned_row)

    return sanitized_data


# =====================================================================
# 2. SEMANTIC SAFETY & SELF-HARM CLASSIFIER (Hybrid Guardrail)
# =====================================================================

# Comprehensive Safety & Harm Categories
SELF_HARM_PATTERNS = [
    r"\b(suicide|self-harm|cut myself|kill myself|end my life|harm myself|want to die|hurt myself)\b",
    r"\b(die|death|cutting|overdose|hanging)\b",
]

INJECTION_PATTERNS = [
    r"\b(ignore (all|previous) (instructions|directives|rules|prompts))\b",
    r"\b(disregard (all|prior) (instructions|guidelines))\b",
    r"\b(you are now (a|an) (unrestricted|jailbroken|helpful assistant|dan))\b",
    r"\b(system prompt:?|override evaluation|give me (a )?score of 10)\b",
    r"\b(forget (your|the) (rules|instructions))\b",
]

DISCRIMINATORY_PATTERNS = [
    r"\b(age|marital status|religion|race|gender|salary history|sexual orientation|ethnicity)\b",
]


def classify_text_safety_guardrail(text: str) -> dict[str, Any]:
    """Semantic & Pattern Safety Classifier: Checks for self-harm, prompt injection, and restricted topics."""
    clean_text = text.strip()
    text_lower = clean_text.lower()

    # 1. Check Self-Harm & Violence Safety Violation
    for pattern in SELF_HARM_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "safe": False,
                "category": "self_harm",
                "reason": "Self-harm or violence content detected.",
            }

    # 2. Check Prompt Injection / Jailbreak Violation
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "safe": False,
                "category": "prompt_injection",
                "reason": "Prompt injection or jailbreak attempt detected.",
            }

    # 3. Check Discriminatory / Restricted Topic Violation
    for pattern in DISCRIMINATORY_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "safe": False,
                "category": "restricted_topic",
                "reason": f"Restricted topic pattern detected matching '{pattern}'",
            }

    return {"safe": True, "category": "clean", "reason": None}


# =====================================================================
# 3. INTERVIEW QUESTION GUARDRAILS
# =====================================================================

def validate_interview_question_guardrail(
    question: str,
    topic: str = "general",
    previous_questions: list[str] | None = None,
) -> dict[str, Any]:
    """Guardrail 3: Validates generated interview questions using hybrid safety classification & deduplication."""
    clean_q = question.strip()

    if len(clean_q) < 10:
        fallback = f"Could you describe your hands-on experience working with {topic}?"
        return {
            "passed": False,
            "reason": "Question too short or empty.",
            "validated_question": fallback,
        }

    # Deduplication check against previous questions
    if previous_questions:
        clean_q_lower = re.sub(r"\W+", " ", clean_q.lower()).strip()
        for prev in previous_questions:
            prev_lower = re.sub(r"\W+", " ", prev.lower()).strip()
            if clean_q_lower == prev_lower or (len(prev_lower) > 15 and prev_lower in clean_q_lower):
                fallback = f"Building on your background, what is a specific problem you solved using {topic} or a related framework?"
                return {
                    "passed": False,
                    "reason": "Duplicate question detected matching previous question.",
                    "category": "duplicate",
                    "validated_question": fallback,
                }

    # Apply hybrid safety classification
    safety_check = classify_text_safety_guardrail(clean_q)
    if not safety_check["safe"]:
        fallback = f"Could you walk me through a technical challenge you solved using {topic}?"
        return {
            "passed": False,
            "reason": safety_check["reason"],
            "category": safety_check["category"],
            "validated_question": fallback,
        }

    return {
        "passed": True,
        "reason": None,
        "category": "clean",
        "validated_question": clean_q,
    }


# =====================================================================
# 4. CANDIDATE ANSWER GUARDRAILS
# =====================================================================

def validate_candidate_answer_guardrail(answer: str) -> dict[str, Any]:
    """Guardrail 4: Validates candidate answers against self-harm, prompt injection, and empty responses."""
    clean_a = answer.strip()

    if len(clean_a) < 3:
        return {
            "passed": False,
            "reason": "Answer is empty or too short.",
            "is_injection": False,
            "is_self_harm": False,
            "sanitized_answer": "No substantial answer provided.",
        }

    # Apply hybrid safety classification
    safety_check = classify_text_safety_guardrail(clean_a)
    if not safety_check["safe"]:
        if safety_check["category"] == "self_harm":
            return {
                "passed": False,
                "reason": "Safety Alert: Self-harm or crisis language detected.",
                "is_injection": False,
                "is_self_harm": True,
                "sanitized_answer": "Safety Alert: If you are experiencing distress, please reach out to national helpline resources.",
            }
        elif safety_check["category"] == "prompt_injection":
            return {
                "passed": False,
                "reason": safety_check["reason"],
                "is_injection": True,
                "is_self_harm": False,
                "sanitized_answer": "Candidate response contained prohibited prompt override commands.",
            }

    return {
        "passed": True,
        "reason": None,
        "is_injection": False,
        "is_self_harm": False,
        "sanitized_answer": clean_a,
    }


# =====================================================================
# 5. RAG & RAGAS EVALUATION FAITHFULNESS GUARDRAIL
# =====================================================================

def validate_evaluation_faithfulness_guardrail(
    question: str,
    contexts: list[str],
    feedback: str,
    threshold: float = 0.75,
) -> dict[str, Any]:
    """Guardrail 5: Uses Ragas metrics to verify evaluation feedback against retrieved context (JD + Resume)."""
    res = ragas_evaluator.evaluate_sample(
        question=question,
        contexts=contexts,
        answer=feedback,
    )

    passed = res.faithfulness >= threshold
    return {
        "passed": passed,
        "passed_guardrail": passed,
        "faithfulness_score": res.faithfulness,
        "answer_relevance_score": res.answer_relevancy,
        "context_precision": res.context_precision,
        "threshold": threshold,
        "feedback": res.feedback,
    }


async def resolve_dual_evaluation_context(
    mcp: Any,
    candidate_id: int,
    job_id: int,
    topic: str = "general",
) -> dict[str, Any]:
    """
    Constructs evaluation context following the Dual-Context Fallback Hierarchy:
    1. Primary: Dual-Context (Both Job Description + Candidate Resume RAG).
    2. Fallback 1: JD-Only Context (if Candidate Resume context is unindexed or missing).
    3. Fallback 2: Generic JD Anchor (if specific JD record is missing).
    """
    jd_chunks: list[str] = []
    resume_chunks: list[str] = []

    # --- Step 1: Fetch Job Description Context (The Primary Anchor) ---
    try:
        if mcp and hasattr(mcp, "search_jd_rag"):
            jd_rag_res = await mcp.search_jd_rag(job_id=job_id, query=topic, top_k=2)
            jd_chunks = jd_rag_res.get("context_chunks", [])
        
        if not jd_chunks and mcp and hasattr(mcp, "get_job_description"):
            jd_info = await mcp.get_job_description(job_id=job_id)
            if jd_info and isinstance(jd_info, dict) and "description" in jd_info:
                desc = jd_info.get("description", "")
                title = jd_info.get("title", f"Job #{job_id}")
                skills = jd_info.get("required_skills", "")
                jd_chunks = [f"[Job Description] Title: {title}. Required Skills: {skills}. Details: {desc}"]
    except Exception:
        jd_chunks = []

    # --- Step 2: Fetch Candidate Resume Context (The Evidence Anchor) ---
    try:
        if mcp and hasattr(mcp, "search_resume_rag"):
            resume_rag_res = await mcp.search_resume_rag(candidate_id=candidate_id, query=topic, top_k=3)
            resume_chunks = resume_rag_res.get("context_chunks", [])
    except Exception:
        resume_chunks = []

    # --- Step 3: Apply Strategy Hierarchy ---
    # Strategy 1: Primary Dual-Context (Both JD + Resume context available)
    if jd_chunks and resume_chunks:
        return {
            "contexts": jd_chunks + resume_chunks,
            "strategy": "dual_context",
            "jd_chunks_count": len(jd_chunks),
            "resume_chunks_count": len(resume_chunks),
        }

    # Strategy 2: Fallback 1 -> JD-Primary Context (Resume unavailable)
    if jd_chunks:
        return {
            "contexts": jd_chunks,
            "strategy": "jd_fallback",
            "jd_chunks_count": len(jd_chunks),
            "resume_chunks_count": 0,
        }

    # Strategy 3: Fallback 2 -> Generic JD Requirement Anchor
    generic_jd = [
        f"[Generic Job Description Anchor] Target expectations for '{topic}': "
        f"Verify core technical skills, problem-solving ability, communication, and job role alignment."
    ]
    return {
        "contexts": generic_jd + resume_chunks if resume_chunks else generic_jd,
        "strategy": "generic_jd_fallback",
        "jd_chunks_count": 1,
        "resume_chunks_count": len(resume_chunks),
    }

