# Agent Instructions & Project Memory

Welcome agent! This file contains project-level directives and rules for the **AI Interview Agent** codebase.

## 📖 Key Rules to Follow

1. **Architectural Decisions**: Read [architectural_decisions.md](file:///c:/Users/chint/Music/AI%20Interview%20Agent/.agents/rules/architectural_decisions.md) before making changes to evaluation, RAGAS, or guardrails.
2. **Dual-Context Evaluation Standard**: All evaluation and RAGAS verification MUST follow the **Dual-Context Fallback Hierarchy**:
   - Primary: Dual Context (JD + Resume)
   - Fallback 1: JD-Only Context
   - Fallback 2: Generic JD Anchor Context
   - *Never ground evaluations exclusively to candidate resumes without JD context.*
3. **Async Evaluation Pattern**: RAGAS evaluation MUST run asynchronously in background tasks or offline scripts to keep real-time UI chat turns sub-second.
4. **Guardrail Integrity**: Always maintain the 5 modular guardrails in `app/guardrails/rules.py` and run `uv run pytest` after modifications.
5. **Model Naming**: Use active Gemini versions (`gemini/gemini-3.6-flash`).

## 📁 Key Documentation References

- [Architecture Overview](file:///c:/Users/chint/Music/AI%20Interview%20Agent/docs/ARCHITECTURE.md)
- [LangGraph Flow](file:///c:/Users/chint/Music/AI%20Interview%20Agent/docs/LANGCHAIN_FLOW.md)
- [API Documentation](file:///c:/Users/chint/Music/AI%20Interview%20Agent/docs/API.md)
- [Decision Log](file:///c:/Users/chint/Music/AI%20Interview%20Agent/docs/DECISION_LOG.md)
