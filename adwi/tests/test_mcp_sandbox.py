"""
Static validation of adwi-sandbox MCP server.
No services, no network — parses AST only.

Guards against stub tools being (re-)advertised as @mcp.tool().
"""
import ast
import pathlib

SERVER = pathlib.Path(__file__).parent.parent / "services" / "mcp" / "adwi-sandbox" / "server.py"


def _mcp_tool_names(src: str) -> set[str]:
    """Return function names decorated with @mcp.tool()."""
    tree = ast.parse(src)
    tools: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            is_mcp_tool = isinstance(deco, ast.Call) and isinstance(
                deco.func, ast.Attribute
            ) and isinstance(deco.func.value, ast.Name) and (
                deco.func.value.id == "mcp" and deco.func.attr == "tool"
            )
            if is_mcp_tool:
                tools.add(node.name)
    return tools


def test_server_syntax():
    """server.py must be syntactically valid Python."""
    src = SERVER.read_text(encoding="utf-8")
    compile(src, str(SERVER), "exec")


def test_run_bash_not_advertised():
    """run_bash must NOT appear as @mcp.tool() — it was removed as a stub.

    If run_bash needs to be re-added, it must be fully implemented with:
      - cwd confined to workspace root
      - blocked paths rejected via PathValidator
      - bounded timeout and output
      - structured JSON return (returncode, stdout, stderr, timed_out)
    Only then should the @mcp.tool() decorator be restored.
    """
    src = SERVER.read_text(encoding="utf-8")
    tools = _mcp_tool_names(src)
    assert "run_bash" not in tools, (
        "run_bash is decorated as @mcp.tool() but was removed as unimplemented. "
        "See adwi/services/mcp/adwi-sandbox/server.py comment for implementation requirements."
    )


def test_all_advertised_tools_have_implementation():
    """Each @mcp.tool() function must contain at least one non-docstring statement.

    A body consisting solely of a docstring + a string-literal return is a stub —
    it should not be decorated as a tool.
    """
    src = SERVER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        is_mcp_tool = any(
            isinstance(d, ast.Call)
            and isinstance(d.func, ast.Attribute)
            and isinstance(d.func.value, ast.Name)
            and d.func.value.id == "mcp"
            and d.func.attr == "tool"
            for d in node.decorator_list
        )
        if not is_mcp_tool:
            continue
        # Strip docstring (first Expr(Constant)) and count real statements
        body = node.body
        real = [
            s for s in body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
            and not (isinstance(s, ast.Return) and isinstance(s.value, ast.Constant))
        ]
        assert real, (
            f"@mcp.tool() '{node.name}' appears to be a stub — body has only "
            "docstring/constant returns. Remove @mcp.tool() or implement the function."
        )
