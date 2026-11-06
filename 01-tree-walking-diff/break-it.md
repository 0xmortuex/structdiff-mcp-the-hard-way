# Break It: Tree Walking

## Challenge 1: Care about key order

Make the object branch also report a difference when `list(a)` and `list(b)` order differ. Which assertion in
`selftest()` fails first, and what would a user of a real config file think of the output?

**Hint:** The very first one. Order-insensitivity is the feature, not an accident.

## Challenge 2: Lose the type check

Delete the `ka != kb` branch. What does `diff({"v": [1]}, {"v": {"a": 1}})` do, and why does it crash rather
than report a change?

**Hint:** The code falls into the `object` branch for one side only. Kind checks are what make every later branch safe.

## Challenge 3: Trust `==`

In `kind()`, test `int` before `bool`. Which test fails? Then find another pair of Python values that `==` treats as
equal but JSON does not (`0` and `False`; `1` and `1.0`). Decide which pairs *should* be equal; you will need the
answer in module 03.

## Challenge 4: A thousand levels deep

Feed `diff` a document nested 5000 levels deep. What happens? How would you protect a server that accepts
documents from strangers? (The real server refuses nesting beyond 100 levels at parse time.)

**Hint:** Python raises `RecursionError`; a limit enforced once at parse time is cheaper than catching it everywhere.
