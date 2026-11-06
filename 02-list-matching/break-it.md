# Break It: List Matching

## Challenge 1: Allow duplicate keys

Remove the `v in seen` check from `pick_key`. Run the duplicate-id case in `selftest()`. What does `match` do with
the second `{"id": 1}` item?

**Hint:** The dict comprehension `{item[f]: j ...}` silently keeps only the last duplicate, so one item is
never paired and never reported. Silent data loss is worse than a noisy fallback.

## Challenge 2: Report every index change as a move

Replace the `lis_members` filter with `if i != j`. How many `moved` entries does the six-item rotation give?

**Hint:** Five instead of one, and the number grows with the list length.

## Challenge 3: A key that is sometimes missing

Remove `"id"` from one item in a list of ten. Which mode does `auto` choose? Is that what you want? (The real server
in `key` mode matches by index *and warns*.)

## Challenge 4: Nested lists

Give each item its own list of records with ids. Does the diff recurse correctly? Why does `label()` use the
*a* index for removed items and the *b* index for added ones?
