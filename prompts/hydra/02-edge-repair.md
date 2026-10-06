The senses below already have an accepted gloss, Dewey code, and T1 form. Do not change lemma, pos, gloss, dewey, t1_decomposition, or depth. Copy them through.

Add edges only.

Both endpoints of an edge must be in the allow-list. The allow-list is every lemma in this batch plus the kernel list in your system instructions.

Drop any edge whose target equals its source. Drop any edge whose target is absent from the allow-list.

Prefer this order when you are sure: hypernym, part_of, antonym, synonym. Skip a relation when you are unsure. An empty edges array is a valid repair.

Return a JSON array with one object per input row, in the same order.

ROWS:
{{ROWS_JSON}}
