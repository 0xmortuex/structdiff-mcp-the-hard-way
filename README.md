# structdiff: The Hard Way

[![Verify](https://github.com/0xmortuex/structdiff-mcp-the-hard-way/actions/workflows/verify.yml/badge.svg)](https://github.com/0xmortuex/structdiff-mcp-the-hard-way/actions/workflows/verify.yml)

Build a semantic-diff MCP server from scratch: the kind that tells an AI agent *what changed*
between two JSON / YAML / CSV files instead of dumping a line diff. You start with a 40-line
tree walk and end with list matching, numeric tolerance, a verified RFC 6902 patch generator, a CSV
row differ, an MCP wrapper tested over real stdio, and a property test that tries to break all of it.

At the end you will have built a minimal version of
[structdiff-mcp](https://github.com/0xmortuex/structdiff-mcp) yourself.

## Why this exists

A diff of two configs that someone re-sorted is 400 changed lines. A diff of two lists where one item
moved to the front is a cascade of edits. `1` and `"1"`, `0.1+0.2` and `0.3`, a missing key and a `null`:
each is a place where the obvious implementation gives an answer that is quietly wrong. This course walks
through each trap, shows the wrong answer, and builds the fix. Every module ends in assertions that run.

## Who this is for

- Developers who have written a "hello world" MCP server and want to build one where the hard part
  is the algorithm, not the SDK
- Anyone who has been bitten by a config diff that lied
- People curious how a JSON Patch generator can be *proved* correct

**Prerequisites:** Python 3.10+ and `pip install -r requirements.txt` (mcp, pyyaml, hypothesis).

## Modules

| # | Module | What you will build |
|---|--------|---------------------|
| 01 | [Tree-Walking Diff](01-tree-walking-diff/) | A recursive diff with readable paths; type changes, null vs missing |
| 02 | [List Matching](02-list-matching/) | Match items by key, by position, or as a set; detect moves with a longest increasing subsequence |
| 03 | [Tolerance and Types](03-tolerance-and-types/) | What "equal" means: tolerance, exact big ints, NaN, ignore globs |
| 04 | [JSON Patch](04-json-patch/) | Generate and apply RFC 6902 patches; the list algorithm; why the order of operations matters |
| 05 | [CSV Row Diffing](05-csv-row-diffing/) | Keyed row diff that streams, with BOMs, delimiter sniffing and duplicate keys |
| 06 | [The MCP Wrapper](06-the-mcp-wrapper/) | Two tools, errors the agent can read, safe YAML, tested through a real stdio client |
| 07 | [Property Testing](07-property-testing/) | Hypothesis proves the patch generator, and catches a planted bug |

Each module contains:
- **`README.md`**: the concepts and design decisions
- **`main.py`**: working, commented code whose self-test is the specification
- **`break-it.md`**: challenges that break your own code, with hints

## How to use this course

**Build along:** read a module, run `python NN-name/main.py`, then do the break-it challenges.
**Reference:** modules 03 and later import earlier modules' `main.py` by path, so keep the folders together.

```
pip install -r requirements.txt
python verify.py          # runs every module for real (a few seconds per module)
python verify.py 04 06    # just these
```

MIT licensed.
