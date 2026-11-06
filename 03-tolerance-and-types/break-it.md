# Break It: Tolerance and Types

## Challenge 1: Use math.isclose

Swap the `Fraction` arithmetic for `math.isclose(x, y, abs_tol=..., rel_tol=...)`. Which assertions fail, and
with what exception?

**Hint:** The big-int ones: `float(2**80) == float(2**80 + 1)` makes the exact check wrong, and `10**400`
overflows.

## Challenge 2: Forget NaN

Remove the NaN branch. A document containing `NaN` now differs from itself. Where would that surface in a
real server? (Hint: `as_json_patch` of a file against itself.)

## Challenge 3: A narrower ignore

Change `".*".join(...)` so `*` only matches inside one path segment (`[^.\[\]]*`). Which ignore case in
`selftest()` breaks, and why is "`*` matches anything" the friendlier rule for `$.meta.*`?

## Challenge 4: Tolerance that is not symmetric

Implement relative tolerance as `delta <= rel_tol * abs(y)`. Show that
`numeric_equal(100, 101, rel_tol=0.01)` and `numeric_equal(101, 100, rel_tol=0.01)` can disagree. Why does the
real code use `max(|x|, |y|)`?
