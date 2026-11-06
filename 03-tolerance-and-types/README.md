# Module 03: Tolerance and Types

## The concept

A diff is only as good as its definition of "equal". Four places where the obvious `==` is wrong.

### 1. Floating point

`0.1 + 0.2 == 0.3` is `False`. Two exports of the same sensor reading differ in the 17th digit. Tolerance fixes
it: **absolute** (`|x-y| <= abs_tol`) for values near zero, **relative** (`|x-y| <= rel_tol * max(|x|,|y|)`)
for values that scale. Pass either.

### 2. Big integers

JSON allows integers of any size and Python keeps them exact: `2**80 != 2**80 + 1`. Converting to float
(`math.isclose`) makes them equal, and for something like `10**400` it raises `OverflowError`. So the
comparison uses `fractions.Fraction`, which represents every int and float *exactly*; the arithmetic never
rounds. (Even `math.isinf(10**400)` overflows, so only floats get asked.)

### 3. NaN and infinity

IEEE says `nan != nan`. For a diff that means a file differs from itself. We declare NaN equal to NaN (and to
nothing else), and an infinity equal only to the same infinity.

### 4. Types

`1` and `1.0` are the same JSON number (Python's `==` agrees, exactly, even for big ints). But `1`, `"1"`
and `true` are three different things: that is the `type_changed` op from module 01.

## Ignore patterns

Real configs contain noise: timestamps, etags, build numbers. `ignore=("*.ts", "$.items[*].etag")` skips them.
Each pattern becomes a regex where `*` means "any text" (dots and brackets included), checked against the
path of every node *before* descending, so an ignored subtree costs nothing. Patterns must start with `$` or
`*`: an unanchored pattern like `ts` is almost certainly a mistake, so it is rejected with a message rather
than guessed at.

## Run it

```
python main.py
```
