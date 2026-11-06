# Module 02: List Matching

## The concept

Arrays are where tree diffs go wrong. Compare these by position:

```
a: [{id:1}, {id:2}, {id:3}]        b: [{id:0}, {id:1}, {id:2}, {id:3}]
```

Position 0 changed id 1 -> 0, position 1 changed 2 -> 1, and so on: seven "changes" for one insertion. A human
sees one added item. The fix is to pair items by **identity** instead of position.

## Strategies

| mode | pairs items by | good for |
|---|---|---|
| `key` | a field (`id`, `name`, `key`) that is present and unique in every item | lists of records |
| `index` | position | genuinely ordered data (coordinates, steps) |
| `set` | equality of the whole item; order ignored, duplicates counted | tag lists, permissions |
| `auto` | `key` if a key field qualifies, else `index` | the sensible default |

### Why "unique" matters

If two items share `id: 1`, "the item with id 1" has no meaning. `pick_key` rejects such a field and `auto` falls
back to position. Guessing would produce confident, wrong diffs.

### Moves and the longest stable subsequence

Once items are paired, order can still differ. If the last of six items jumps to the front, naive logic says
*every* index changed. But five of them kept their relative order. Only one item travelled.

Take the b-index of each pair, sorted by a-index: `[5, 0, 1, 2, 3, 4]`. A **longest increasing subsequence**
(`0 1 2 3 4`) is the set that stayed put; everything else (`5`) moved. `lis_members` finds it in O(n log n) with
patience sorting (`bisect` on the pile tops). The result is one `moved` entry.

## Run it

```
python main.py
```

`match()` returns `{"pairs", "removed", "added", "key"}`. Module 03's diff and module 04's patch generator both
consume exactly that shape, which is why the diff and the patch cannot disagree about what a list did.
