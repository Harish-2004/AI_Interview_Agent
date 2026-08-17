# LangChain & LangGraph Flow

This document details the orchestrator architecture of the **AI Interview Agent**, explaining how it utilizes LangGraph and LangChain to execute a stateful, multi-agent, human-in-the-loop technical interview.

---

## Why LangGraph?

Standard **LangChain** structures are designed for linear, direct pipelines (e.g. Prompt $\rightarrow$ LLM $\rightarrow$ Output Parser). However, a technical interview is non-linear and stateful:
1. **Looping**: The agent must loop through a list of skills, asking questions one by one.
2. **Persistence**: The orchestrator must remember what was asked, the candidate's previous responses, and evaluation scores.
3. **Human-in-the-Loop**: The conversation must pause (interrupt) to wait for candidate input and then resume from the exact same execution point without losing context.

**LangGraph** solves this by representing the interview as a **State Graph** (a finite state machine with memory checkpointers).

---

## Core Architecture Overview

The interaction flow is structured as follows:

```mermaid
sequence diagram
    actor Candidate
    participant API as FastAPI API Layer
    participant LG as LangGraph Orchestrator
    participant DB as SQLite DB
    participant AG as Agent Nodes (LLM)
    participant MCP as MCP Handlers (In-Process)

    %% Session Initiation
    Candidate ->> API: POST /interviews (candidate_id, job_id)
    activate API
    API ->> DB: Create interview record (status=in_progress)
    API ->> LG: compile & graph.ainvoke(initial_state)
    activate LG

    %% Planner & Interviewer Node execution
    LG ->> MCP: Fetch Job required skills
    LG ->> AG: run_planner (Pick next topic)
    LG ->> MCP: Fetch candidate resume
    LG ->> AG: run_interviewer (Generate question)
    LG ->> LG: interrupt(current_question) & save state
    deactivate LG
    LG -->> API: Suspended state with question
    API ->> DB: Save generated question to interview_message
    API -->> Candidate: HTTP Response (current_question)
    deactivate API

    %% Resumption and Evaluation
    Candidate ->> API: POST /interviews/{id}/messages (answer)
    activate API
    API ->> LG: graph.ainvoke(Command(resume=answer))
    activate LG
    LG ->> AG: run_evaluator (Score answer)
    LG ->> MCP: store_answer & update covered skills
    LG ->> LG: Evaluate remaining skills & max questions
    
    %% Loop check
    alt should_continue is True
        LG ->> AG: run_planner (Pick next skill)
        LG ->> AG: run_interviewer (Generate question)
        LG ->> LG: interrupt(current_question)
        LG -->> API: Suspended state with question
    else should_continue is False
        LG ->> AG: run_report (Summarize interview)
        LG ->> LG: Transitions to END
        LG -->> API: Finished state with report summary
        API ->> DB: Update interview (status=completed)
    end
    deactivate LG
    API ->> DB: Save answer & evaluations
    API -->> Candidate: HTTP Response (next_question OR final report)
    deactivate API
```

---

## 1. Graph State Definition

The shared state of the execution graph is defined as `InterviewState` in [interview_graph.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/graphs/interview_graph.py#L15-L29):

```python
class InterviewState(TypedDict, total=False):
    interview_id: int              # DB interview primary key
    candidate_id: int              # Candidate primary key
    job_id: int                    # Job description primary key
    covered_skills: list[str]      # List of technical skills already evaluated
    remaining_skills: list[str]    # List of technical skills still to evaluate
    current_topic: str             # Current skill topic being evaluated
    current_question: str          # Current question asked by interviewer
    last_answer: str               # Candidate's answer to current_question
    question_count: int            # Counter of questions asked
    evaluations: list[dict]        # Per-topic scoring and feedback history
    should_continue: bool          # Flag determining whether to loop or end
    report: dict                   # Final structured hiring report
    messages: Annotated[list, add_messages] # Optional conversational history
```

---

## 2. Graph Nodes & Agents

The graph contains five primary nodes defined in [interview_graph.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/graphs/interview_graph.py#L31-L70):

### A. Planner Node (`planner`)
*   **Code Location**: [planner/agent.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/agents/planner/agent.py)
*   **Logic**:
    1. Reads `covered_skills` and `remaining_skills`.
    2. If `remaining_skills` is empty but there's a `job_id`, it calls the Job Description MCP server (`mcp.get_required_skills`) to populate remaining skills.
    3. If there are skills left in `remaining_skills`, it picks the first one.
    4. If no skills are defined in the JD, it invokes the **Planner LLM** to decide the next topic dynamically.
    5. Saves the selected topic to `state["current_topic"]`.

### B. Interviewer Node (`interviewer`)
*   **Code Location**: [interviewer/agent.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/agents/interviewer/agent.py)
*   **Logic**:
    1. Fetches candidate resume details from the Resume MCP server (`mcp.get_resume`).
    2. Fetches the job description details from the JD MCP server (`mcp.get_job_description`).
    3. Fetches history from the Memory MCP server (`mcp.get_previous_questions`).
    4. Constructs a prompt incorporating `current_topic` and context, then asks the **Interviewer LLM** to formulate a technical question.
    5. Updates `state["current_question"]` and increments `question_count`.

### C. Wait Node (`wait_for_answer`)
*   **Code Location**: [interview_graph.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/graphs/interview_graph.py#L40)
*   **Logic**:
    1. Calls `interrupt({"question": state.get("current_question", "")})`.
    2. This pauses the graph, saves the state snapshot using `MemorySaver`, and yields control back to the FastAPI endpoint.
    3. The graph remains paused until a resume command is received containing the candidate's answer.

### D. Evaluator Node (`evaluator`)
*   **Code Location**: [evaluator/agent.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/agents/evaluator/agent.py)
*   **Logic**:
    1. Takes the `current_question`, the candidate's `last_answer`, and the assessed `current_topic`.
    2. Sends them to the **Evaluator LLM** to score the answer (from 1 to 10) and generate feedback (strengths, weaknesses).
    3. Invokes the Memory MCP server (`mcp.store_answer`) to save the performance details.
    4. Updates the state: appends evaluation to `evaluations`, adds topic to `covered_skills`, and removes it from `remaining_skills`.
    5. Evaluates loop condition: `should_continue` is `True` if there are still `remaining_skills` AND `question_count` is less than `MAX_QUESTIONS`.

### E. Report Node (`report`)
*   **Code Location**: [report/agent.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/agents/report/agent.py)
*   **Logic**:
    1. Aggregates all evaluations from the state (or queries them via `mcp.get_scores`).
    2. Passes the data to the **Report LLM** to produce a structured JSON hiring recommendation.
    3. Sets `state["report"]` and marks `should_continue = False`.

---

## 3. Human-in-the-Loop State Machine Lifecycle

The graph compilation and execution are controlled by the `InterviewService` class in [interview_service.py](file:///c:/Users/chint/Music/AI%20Interview%20Agent/backend/app/services/interview_service.py):

### Phase 1: Creating and Starting the Session
When `/interviews` is called:
1. `InterviewService.start_interview` compiles the graph with a thread identifier:
   ```python
   config = {"configurable": {"thread_id": str(interview.id)}}
   ```
2. The graph starts executing asynchronously:
   ```python
   await graph.ainvoke(initial_state, config)
   ```
3. It runs `planner` $\rightarrow$ `interviewer` $\rightarrow$ `wait_for_answer` where the execution hits `interrupt()` and stops.
4. The service reads the state snapshot, saves the interviewer's question to the SQL database table `interview_message`, and returns the question to the candidate.

### Phase 2: Responding and Resuming
When `/interviews/{id}/messages` is called:
1. `InterviewService.submit_answer` compiles the graph for the same `thread_id`.
2. It resumes the graph by sending a `Command(resume=answer)`:
   ```python
   await graph.ainvoke(Command(resume=answer), config)
   ```
3. The graph resumes directly from `wait_for_answer` node, maps the resumed value to `state["last_answer"]`, and moves to `evaluator`.
4. Based on the evaluator's output, it either loops back to `planner` (which starts a new question sequence and hits `interrupt` again) or proceeds to `report` and exits.
5. The service persists all evaluations and messages to the SQL database.

---

## 4. How to Extend or Customize the Flow

* **Add a new agent step**: 
  1. Define a node function in `interview_graph.py`.
  2. Register it with `graph.add_node("node_name", node_func)`.
  3. Set up the routing using `graph.add_edge` or `graph.add_conditional_edges`.
* **Change routing logic**:
  1. Edit `route_after_evaluator` in `interview_graph.py`. For example, you could check if the candidate's average score is below a certain threshold to fast-fail/terminate the interview early.
* **Integrate live tools**:
  1. All agents consume the `MCPClient` which routes requests to in-process domain handlers (`app/mcp/handlers.py`).
  2. To link to real external tools (e.g. Jira, GitHub, or ATS systems), simply modify/add methods in the MCP handlers.
