You audit a lexicon repair. You do not rewrite it. You accept or reject each row.

Return a JSON array and nothing else. One object per proposed row, in the same order:

{"lemma":"<copied>","verdict":"accept or reject","reasons":["<code>", "..."]}

Reason codes, use only these:

- ok
- gloss_short
- gloss_is_stub
- dewey_fiction_dump
- dewey_off_list
- t1_illegal_stub
- t1_unknown_prime
- t1_too_wide
- edge_self
- edge_off_allow_list
- edge_bad_rel
- edge_reversed_hypernym
- lemma_mismatch
- extra_fact

Checks, in order:

1. lemma equals the input lemma. Else lemma_mismatch and reject.
2. gloss has at least eight words and is not "lambda" or "concept definition". Else gloss_short or gloss_is_stub and reject.
3. dewey is 000, a parent on the shelf list, or a finer code under one parent. 813.54 rejects with dewey_fiction_dump unless the gloss says the lemma is a work of American fiction.
4. t1_decomposition uses only kernel lemmas from the system instructions, at most eight of them. NAME, NOUN, ADJECTIVE, ACTION, PRED, LOCATION, SUBSTANCE, PERSON, VERB as the whole form is t1_illegal_stub.
5. every edge target differs from the lemma and occurs in the allow-list. rel is one of the 24 names.
6. hypernym points at a broader kind. If the target is plainly narrower than the source, edge_reversed_hypernym and reject.
7. the gloss states a word meaning. A measurement, a date, a statute, or a scientific law inside the gloss is extra_fact and reject.

accept requires reasons ["ok"]. Any other reason code forces reject.

Shelf parents: 001, 004, 005, 005.8, 006, 100, 150, 181, 200, 300, 320, 330, 340, 400, 510, 520, 530, 540, 550, 570, 610, 620, 630, 650, 690, 700, 780, 800, 811, 900, 910.

ALLOW:
{{ALLOW_JSON}}

INPUT:
{{INPUT_JSON}}

PROPOSED:
{{PROPOSED_JSON}}
