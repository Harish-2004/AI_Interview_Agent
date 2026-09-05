"""Script to generate visual graph diagram (PNG, Mermaid, and Markdown) for the LangGraph workflow."""

import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graphs.interview_graph import compile_interview_graph


class DummyMCPClient:
    pass


def main():
    compiled_graph = compile_interview_graph(DummyMCPClient())
    graph_obj = compiled_graph.get_graph()

    # 1. Mermaid Code
    mermaid_code = graph_obj.draw_mermaid()
    
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    mermaid_path = os.path.join(docs_dir, "interview_graph.mmd")
    with open(mermaid_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    print(f"Generated Mermaid graph file: docs/interview_graph.mmd")

    # 2. Try PNG Image Generation via Mermaid API
    try:
        png_bytes = graph_obj.draw_mermaid_png()
        png_path = os.path.join(docs_dir, "interview_graph.png")
        with open(png_path, "wb") as f:
            f.write(png_bytes)
        print(f"Generated graph image PNG: docs/interview_graph.png")
    except Exception as exc:
        print(f"Could not render PNG directly ({exc}). You can view docs/interview_graph.mmd or GitHub Markdown.")

    # 3. Print Mermaid Code directly
    print("\n==========================================")
    print("      LANGGRAPH MERMAID GRAPH DIAGRAM     ")
    print("==========================================\n")
    print("```mermaid")
    print(mermaid_code)
    print("```")


if __name__ == "__main__":
    main()
