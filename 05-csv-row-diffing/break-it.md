# Break It: CSV

## Challenge 1: Read as plain UTF-8

Change `encoding_for` to always return `"utf-8"`. Which part of `selftest()` fails first, and why does the error
mention a missing key column rather than an encoding?

## Challenge 2: Use csv.Sniffer

Replace `sniff` with `csv.Sniffer().sniff(sample).delimiter`. Try it on `"a;b\n1;2\n"`. Does it get small files
right? What does it do on a single-column file?

## Challenge 3: Dict instead of list of rows

Change the index to `dict[key] -> row`. Which test fails, and what happens to the second `id=1` row in file a?

## Challenge 4: Hold both files

Load b into memory too. Measure peak memory (`tracemalloc`) on the 50,000-row case against the streaming version.
At what file size does it start to matter?
