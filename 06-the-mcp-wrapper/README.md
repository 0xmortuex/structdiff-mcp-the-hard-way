# Module 06: The MCP Wrapper

## The concept

The engine is done. Wrapping it takes little code, and almost all of the value is in three decisions.

### 1. Tool design

Two tools, not twelve: `diff_text` and `as_json_patch`. Parameter names an agent can guess (`a`, `b`, `format`),
sensible defaults (`array_match="auto"`), and `Literal[...]` types so the JSON schema lists the legal values.
The **docstring is the tool description** the model reads: what the tool does, what it returns, what the ops
mean. Write it for a reader who cannot see your code.

### 2. Errors the agent can read

In `mcp>=2`, if a tool raises an ordinary exception the client only sees a generic "error executing tool"; the
message is hidden on purpose because it might leak internals. The one exception that passes its text through is
`ToolError`. So the `tool()` decorator converts *expected* failures (`UserError`, `ValueError`) to `ToolError`
at the boundary and lets genuine bugs stay hidden. "a is not valid json: Expecting property name ... line 1
column 2" lets the agent fix its input and retry; "error" does not.

### 3. Safety

YAML's full loader can construct arbitrary Python objects: `!!python/object/apply:os.system ["..."]` runs a
command. `yaml.safe_load` refuses those tags. The test sends such a document over the wire and asserts it is
rejected with a readable error.

## Verifying through the real protocol

`drive()` launches this very file with `--serve` as a subprocess and speaks MCP to it through the official client
(`stdio_client`, `ClientSession`): `initialize`, `list_tools`, `call_tool`. That is what Claude Desktop does, so what
passes here is what works in the product. A unit test of `diff_text()` alone would not catch a broken schema, a
stdout print that corrupts the protocol, or a swallowed error message.

## Run it

```
python main.py            # runs the client test
python main.py --serve    # what a client would launch
```

The tutorial server reads text, not files. The full server adds a read-only `--dir` sandbox: file paths are
resolved with `realpath` (so a symlink cannot escape) and anything outside the allowed folders is refused.
