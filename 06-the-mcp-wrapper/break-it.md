# Break It: The MCP Wrapper

## Challenge 1: Print to stdout

Add `print("debug")` inside `diff_text`. Run `python main.py`. What happens, and why is stdout sacred on a stdio
server?

**Hint:** stdout *is* the protocol channel; stray bytes corrupt the JSON-RPC stream. Log to stderr.

## Challenge 2: Raise a plain exception

In `parse`, let a plain `RuntimeError` escape instead of `UserError`. What text does the client see now, and how
would an agent recover from it?

## Challenge 3: An unsafe YAML loader

In a scratch copy, replace `yaml.safe_load(text)` with `yaml.load(text, Loader=yaml.UnsafeLoader)` and send
`x: !!python/object/apply:os.getcwd []`. Watch the call actually happen (`os.getcwd` is harmless), then put
`safe_load` back.

## Challenge 4: Unbounded output

Remove `max_changes`, then diff two 100,000-key documents. What does the agent's context window look like? Why
does the real server keep exact counts but cap the listed changes?
