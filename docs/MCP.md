# MCP Design

## Philosophy

MCP (Model Context Protocol) servers expose **tools** that agents call for domain data. We implement custom in-repo servers first — no external integrations required for the demo.

When ATS integration arrives, add an **ATS MCP** server. Agents and the graph do not change; only the MCP client configuration gains a new server.

## Server Registry

| Server | Module | Transport |
|--------|--------|-----------|
| Resume MCP | `app/mcp/resume_server/` | stdio (dev) / in-process (tests) |
| JD MCP | `app/mcp/jd_server/` | stdio (dev) / in-process (tests) |
| Interview Memory MCP | `app/mcp/memory_server/` | stdio (dev) / in-process (tests) |

## Resume MCP

| Tool | Parameters | Returns |
|------|------------|---------|
| `get_resume` | `candidate_id: int` | Full resume text and metadata |
| `extract_skills` | `candidate_id: int` | List of skills inferred from resume |
| `get_experience` | `candidate_id: int` | Work experience summary |

## JD MCP

| Tool | Parameters | Returns |
|------|------------|---------|
| `get_job_description` | `job_id: int` | Job title and full description |
| `get_required_skills` | `job_id: int` | Required skills from JD |

## Interview Memory MCP

| Tool | Parameters | Returns |
|------|------------|---------|
| `store_answer` | `interview_id, question, answer, score` | Confirmation |
| `get_previous_questions` | `interview_id: int` | List of prior questions |
| `get_scores` | `interview_id: int` | All skill scores for interview |

## MCP Client

`app/mcp/client.py` provides:

- `MCPClient` — connects to servers via stdio subprocess or in-process handlers.
- `get_mcp_client(db_session)` — factory used by agents and services.

Agents call tools through the client rather than hitting the database directly, keeping a clean separation between orchestration and data access.

## Future: ATS MCP

```python
# app/mcp/ats_server/server.py
@mcp.tool()
async def fetch_candidate_from_ats(ats_candidate_id: str) -> dict: ...

@mcp.tool()
async def push_interview_result(interview_id: int, report: dict) -> dict: ...
```

Register in client config:

```yaml
mcp_servers:
  - name: ats
    command: python -m app.mcp.ats_server.server
```

No changes to Planner, Interviewer, Evaluator, or Report agents.

## Running MCP Servers Standalone

```bash
cd backend
uv run python -m app.mcp.resume_server.server
uv run python -m app.mcp.jd_server.server
uv run python -m app.mcp.memory_server.server
```

Each server speaks MCP over stdio for IDE/tooling integration.
