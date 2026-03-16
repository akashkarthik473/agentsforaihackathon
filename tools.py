"""
Repository tools for the firmware triage agent.
These are the three tools the agent can call to inspect the demo codebase.

Person B: wire these into your agent's tool-calling loop.
The tool definitions for the model are in TOOL_DEFINITIONS below.
"""

from pathlib import Path

DEMO_ROOT = Path("demo_repo")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def list_repo_files() -> str:
    """Return a newline-separated list of every file in the demo repo."""
    files = sorted(
        str(p.relative_to(DEMO_ROOT))
        for p in DEMO_ROOT.rglob("*")
        if p.is_file()
    )
    return "\n".join(files)


def read_file(path: str) -> str:
    """Read and return the contents of a file inside the demo repo.

    Args:
        path: Relative path within demo_repo (e.g. "bms_interface.c").
    """
    target = DEMO_ROOT / path
    if not target.is_file():
        return f"Error: file not found: {path}"
    return target.read_text(encoding="utf-8")


def search_repo(query: str) -> str:
    """Search all files in the demo repo for lines containing *query*.

    Returns matching lines with file path and line number.

    Args:
        query: Case-insensitive substring to search for.
    """
    results = []
    query_lower = query.lower()
    for p in sorted(DEMO_ROOT.rglob("*")):
        if not p.is_file():
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
                if query_lower in line.lower():
                    rel = str(p.relative_to(DEMO_ROOT))
                    results.append(f"{rel}:{i}: {line.strip()}")
        except (UnicodeDecodeError, PermissionError):
            continue
    if not results:
        return "No results found."
    return "\n".join(results)


# ---------------------------------------------------------------------------
# Dispatcher — maps tool name string to function
# ---------------------------------------------------------------------------

TOOL_DISPATCH = {
    "list_repo_files": lambda _args: list_repo_files(),
    "read_file": lambda args: read_file(args["path"]),
    "search_repo": lambda args: search_repo(args["query"]),
}


def call_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return the string result."""
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return f"Error: unknown tool '{name}'"
    return fn(arguments)


# ---------------------------------------------------------------------------
# Tool definitions for the model (OpenAI function-calling format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_repo_files",
            "description": "List all files in the firmware repository.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the firmware repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file, e.g. 'bms_interface.c'",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_repo",
            "description": "Search all files in the repository for lines matching a query string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Case-insensitive substring to search for",
                    }
                },
                "required": ["query"],
            },
        },
    },
]
