"""Tests for Generic DB MCP Server, LlamaIndex RAG Service, and Ragas Evaluator."""

import pytest
from unittest.mock import AsyncMock
from app.eval.ragas_evaluator import ragas_evaluator
from app.graphs.interview_graph import build_interview_graph
from app.mcp.generic_db_server.server import describe_table, execute_read_query, get_tables
from app.services.rag_service import rag_service


@pytest.mark.asyncio
async def test_generic_db_mcp_server_tools():
    from unittest.mock import AsyncMock, patch
    with patch("app.mcp.generic_db_server.server.db_mcp_client.list_database_structures", new=AsyncMock(return_value={"status": "success", "structures": {"postgresql": {"tables": ["candidates"]}}})), \
         patch("app.mcp.generic_db_server.server.db_mcp_client.describe_database_schema", new=AsyncMock(return_value={"status": "success", "table": "candidates", "columns": []})), \
         patch("app.mcp.generic_db_server.server.db_mcp_client.execute_safe_query", side_effect=lambda q, **kw: {"status": "error", "message": "Security Error: Only read-only SELECT queries are allowed."} if "DELETE" in q else {"status": "success", "data": [{"test_val": 1}]}):
        
        # 1. Test get_tables
        tables_res = await get_tables()
        assert tables_res["status"] == "success"
        assert isinstance(tables_res["tables"], list)

        # 2. Test describe_table if tables exist
        desc_res = await describe_table("candidates")
        assert desc_res["status"] == "success"
        assert desc_res["table"] == "candidates"

        # 3. Test execute_read_query safe SELECT
        query_res = await execute_read_query("SELECT 1 AS test_val;")
        assert query_res["status"] == "success"
        assert query_res["data"][0]["test_val"] == 1

        # 4. Test security block on mutation queries
        bad_res = await execute_read_query("DELETE FROM candidates;")
        assert bad_res["status"] == "error"
        assert "Security Error" in bad_res["message"]



def test_llama_index_rag_service():
    candidate_id = 999
    resume = """
    Jane Doe - Python Microservices Architect.
    Experience: 5 years designing FastAPI backend services and managing PostgreSQL databases.
    Built Docker containerization pipelines.
    """
    
    rag_service.index_resume(candidate_id, resume)
    retrieved = rag_service.retrieve_resume_context(candidate_id, "FastAPI backend services", top_k=2)
    
    assert len(retrieved) > 0
    assert any("FastAPI" in c or "Python" in c for c in retrieved)


def test_ragas_evaluator():
    question = "What is Jane Doe's experience with FastAPI?"
    contexts = ["Jane Doe has 5 years designing FastAPI backend services and managing PostgreSQL databases."]
    answer = "Jane Doe has 5 years of experience building FastAPI microservices and PostgreSQL databases."

    result = ragas_evaluator.evaluate_sample(
        question=question,
        contexts=contexts,
        answer=answer,
    )

    assert result.faithfulness > 0.5
    assert result.answer_relevancy > 0.5
    assert result.passed_guardrail is True


@pytest.mark.asyncio
async def test_langgraph_ragas_reflection_state():
    """Verify that LangGraph state updates correctly when Ragas reflection guardrails trigger."""
    mcp_mock = AsyncMock()
    mcp_mock.search_resume_rag.return_value = {"context_chunks": ["Candidate knows Python."]}
    
    graph_builder = build_interview_graph(mcp_mock)
    
    # Simulate initial state where Ragas guardrail failed (low faithfulness)
    initial_state = {
        "candidate_id": 1,
        "current_question": "Do you know Python?",
        "last_answer": "Yes, I built Python apps.",
        "evaluations": [{"skill": "Python", "score": 3, "feedback": "Candidate claims 10 years experience."}],
        "ragas_eval": {"faithfulness": 0.2, "passed_guardrail": False, "feedback": "Unsupported claim."},
        "reflection_count": 0,
        "should_continue": True,
    }

    # Execute reflection node directly
    nodes_dict = {node_id: func for node_id, func in graph_builder.nodes.items()}
    reflection_func = nodes_dict["reflection"].runnable

    updated_state = await reflection_func.ainvoke(initial_state)

    # Assert state was updated correctly
    assert updated_state["reflection_count"] == 1
    assert len(updated_state["reflection_log"]) == 1
    assert "Reflection #1" in updated_state["reflection_log"][0]
    assert updated_state["ragas_eval"]["passed_guardrail"] is True
    assert "Reflected:" in updated_state["evaluations"][-1]["feedback"]
