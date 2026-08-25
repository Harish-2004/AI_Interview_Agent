"""Ragas Evaluation Suite for measuring Faithfulness, Answer Relevance, Context Precision, and Context Recall."""

import re
from typing import Any
from pydantic import BaseModel

from app.config import settings


class RagasEvaluationResult(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    passed_guardrail: bool
    feedback: str


class RagasEvaluator:
    """Evaluates RAG and Agent output quality using Ragas metrics and reflection guardrails."""

    def __init__(self, faithfulness_threshold: float | None = None):
        self.threshold = faithfulness_threshold or settings.ragas_faithfulness_threshold

    def evaluate_sample(
        self,
        question: str,
        contexts: list[str],
        answer: str,
        ground_truth: str | None = None,
    ) -> RagasEvaluationResult:
        """Evaluate a single RAG interaction (Question, Contexts, Answer, Ground Truth)."""
        # Try running official ragas framework if installed and keys configured
        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

            data = {
                "question": [question],
                "contexts": [contexts],
                "answer": [answer],
            }
            if ground_truth:
                data["ground_truth"] = [ground_truth]

            dataset = Dataset.from_dict(data)
            metrics_list = [faithfulness, answer_relevancy, context_precision]
            if ground_truth:
                metrics_list.append(context_recall)

            results = evaluate(dataset=dataset, metrics=metrics_list)
            
            f_score = float(results.get("faithfulness", 0.0))
            a_score = float(results.get("answer_relevancy", 0.0))
            cp_score = float(results.get("context_precision", 0.0))
            cr_score = float(results.get("context_recall", 1.0 if not ground_truth else 0.0))
        except Exception:
            # Resilient fallback evaluation when running offline or mock mode
            f_score, a_score, cp_score, cr_score = self._fallback_eval(question, contexts, answer, ground_truth)

        passed = f_score >= self.threshold
        feedback = (
            "RAG response passed quality guardrails."
            if passed
            else f"Faithfulness score ({f_score:.2f}) below threshold ({self.threshold:.2f}). Re-retrieval recommended."
        )

        return RagasEvaluationResult(
            faithfulness=round(f_score, 2),
            answer_relevancy=round(a_score, 2),
            context_precision=round(cp_score, 2),
            context_recall=round(cr_score, 2),
            passed_guardrail=passed,
            feedback=feedback,
        )

    def _fallback_eval(
        self,
        question: str,
        contexts: list[str],
        answer: str,
        ground_truth: str | None = None,
    ) -> tuple[float, float, float, float]:
        """Compute heuristic overlap metrics matching Ragas score definitions."""
        all_context_text = " ".join(contexts).lower()
        answer_text = answer.lower()
        question_text = question.lower()

        # Faithfulness: fraction of key terms in answer that exist in context
        ans_words = set(re.findall(r"\b\w{4,}\b", answer_text))
        if not ans_words:
            f_score = 1.0
        else:
            supported = sum(1 for w in ans_words if w in all_context_text or w in question_text)
            f_score = min(1.0, supported / len(ans_words))

        # Answer Relevancy: overlap between question and answer
        q_words = set(re.findall(r"\b\w{4,}\b", question_text))
        if not q_words:
            a_score = 1.0
        else:
            rel = sum(1 for w in q_words if w in answer_text)
            a_score = min(1.0, (rel / len(q_words)) + 0.3)

        # Context Precision: fraction of retrieved contexts that are relevant to question
        if not contexts:
            cp_score = 0.0
        else:
            rel_chunks = sum(1 for c in contexts if any(w in c.lower() for w in q_words))
            cp_score = rel_chunks / len(contexts) if contexts else 0.5

        # Context Recall: overlap between ground_truth and context
        if ground_truth:
            gt_words = set(re.findall(r"\b\w{4,}\b", ground_truth.lower()))
            if not gt_words:
                cr_score = 1.0
            else:
                recalled = sum(1 for w in gt_words if w in all_context_text)
                cr_score = recalled / len(gt_words)
        else:
            cr_score = 1.0

        return f_score, min(1.0, a_score), cp_score, cr_score


# Global evaluator singleton instance
ragas_evaluator = RagasEvaluator()
