"""Module 06: wrap the engine in an MCP server, and test it the way a real client would.

Run:  python main.py            # starts the server as a subprocess and talks MCP to it
      python main.py --serve    # run it as an actual stdio server (what a client launches)
"""

from __future__ import annotations

import asyncio
import functools
import importlib.util
import json
import pathlib
import sys
from collections.abc import Callable
from typing import Any, Literal, TypeVar

import yaml
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


def load(dirname: str) -> Any:
    path = pathlib.Path(__file__).resolve().parent.parent / dirname / "main.py"
    name = "m_" + dirname.replace("-", "_")
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


engine = load("03-tolerance-and-types")
patching = load("04-json-patch")

mcp = MCPServer(
    "minidiff",
    instructions="Semantic diffs of JSON/YAML text. diff_text lists changes by path; as_json_patch "
    "returns an RFC 6902 patch turning a into b.",
)

F = TypeVar("F", bound=Callable[..., Any])


class UserError(Exception):
    """Something the caller can fix. Its message is written for the agent."""


def tool(fn: F) -> F:
    """Register fn as a tool. mcp>=2 hides every exception message from the client EXCEPT
    ToolError, so expected failures are converted here - one place, not in every tool."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except (UserError, ValueError) as e:
            raise ToolError(str(e)) from e

    mcp.tool()(wrapper)
    return fn


def parse(text: str, fmt: str, label: str) -> Any:
    try:
        if fmt == "json":
            return json.loads(text)
        # safe_load only. yaml.load() with the default loader would run `!!python/object/apply`.
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise UserError(f"{label} is not valid {fmt}: {e}") from None


@tool
def diff_text(
    a: str,
    b: str,
    format: Literal["json", "yaml"] = "json",
    array_match: Literal["auto", "index", "set"] = "auto",
    abs_tol: float = 0.0,
    ignore: list[str] | None = None,
    max_changes: int = 100,
) -> dict[str, Any]:
    """Semantic diff of two JSON or YAML documents given as text.

    Ignores key order and formatting. Lists of objects are matched by an id/name/key field,
    so reordering is reported as 'moved'. Returns {identical, total, changes[]}; each change is
    {op, path, old, new} with op one of added, removed, changed, type_changed, moved.
    """
    changes = engine.diff(parse(a, format, "a"), parse(b, format, "b"), array_match, abs_tol, 0.0, tuple(ignore or ()))
    shown = [{"op": op, "path": path, "old": old, "new": new} for op, path, old, new in changes[:max_changes]]
    return {"identical": not changes, "total": len(changes), "changes": shown}


@tool
def as_json_patch(a: str, b: str, format: Literal["json", "yaml"] = "json") -> dict[str, Any]:
    """RFC 6902 JSON Patch that turns document a into document b (both given as text).

    The patch is applied to a before it is returned; if the result is not b the call fails
    rather than hand back a patch that does not work.
    """
    da, db = parse(a, format, "a"), parse(b, format, "b")
    ops = patching.make_patch(da, db)
    if not patching.same(patching.apply_patch(da, ops), db):
        raise RuntimeError("internal error: patch does not reproduce b")
    return {"operations": len(ops), "patch": ops}


# --------------------------------------------------------------- a real client


async def drive() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=[__file__, "--serve"], env={"PYTHONIOENCODING": "utf-8"}
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
        assert names == {"diff_text", "as_json_patch"}, names

        a = json.dumps({"users": [{"id": 1, "r": "x"}, {"id": 2, "r": "y"}], "v": 0.1 + 0.2})
        b = json.dumps({"v": 0.3, "users": [{"id": 2, "r": "y"}, {"id": 1, "r": "z"}]})
        res = await session.call_tool("diff_text", {"a": a, "b": b, "abs_tol": 1e-9})
        assert not res.is_error
        out = json.loads(res.content[0].text)
        assert [c["op"] for c in out["changes"]] == ["changed", "moved"], out

        res = await session.call_tool("diff_text", {"a": "a: 1\nb: [1, 2]", "b": "b: [1, 2]\na: 1", "format": "yaml"})
        assert json.loads(res.content[0].text)["identical"]

        res = await session.call_tool("as_json_patch", {"a": a, "b": b})
        patch = json.loads(res.content[0].text)["patch"]
        assert patching.same(patching.apply_patch(json.loads(a), patch), json.loads(b))

        # Errors must arrive as readable text, flagged as errors.
        res = await session.call_tool("diff_text", {"a": "{", "b": "{}"})
        assert res.is_error and "a is not valid json" in res.content[0].text, res.content
        # And the safe YAML loader must refuse code-execution tags.
        evil = "x: !!python/object/apply:os.getcwd []"
        res = await session.call_tool("diff_text", {"a": evil, "b": "x: 1", "format": "yaml"})
        assert res.is_error and "not valid yaml" in res.content[0].text, res.content
    print("module 06 OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run()
    else:
        asyncio.run(drive())
