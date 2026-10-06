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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "assembly", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "breakfast", "can", "clean", "cold", "color", "combination", "creature", "customer", "cut", "dark", "desire", "die", "do", "dont-want", "draft", "drink", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "humans", "hundreds", "i", "if", "inside", "kind", "know", "land", "light", "like", "little", "live", "make", "markets", "maybe", "medium", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "plant", "pull", "push", "put", "round", "run", "same", "say", "see", "side", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "stone", "straight", "sun", "take", "there-is", "think", "this", "touch", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "wood", "words", "you"]

INPUT:
[
  {
    "id": 2263,
    "lemma": "assembly",
    "pos": "N",
    "gloss": "gathering",
    "dewey": "302",
    "t1_decomposition": "GATHER(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "gathering",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2264,
    "lemma": "breakfast",
    "pos": "N",
    "gloss": "morning meal",
    "dewey": "641",
    "t1_decomposition": "MEAL(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "meal",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2270,
    "lemma": "combination",
    "pos": "N",
    "gloss": "mixture",
    "dewey": "001",
    "t1_decomposition": "MIXTURE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "mixture",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2272,
    "lemma": "customer",
    "pos": "N",
    "gloss": "buyer",
    "dewey": "658",
    "t1_decomposition": "BUYER(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "buyer",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 2274,
    "lemma": "desire",
    "pos": "N",
    "gloss": "wish",
    "dewey": "152",
    "t1_decomposition": "WISH(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "synonym",
        "target": "wish",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 2276,
    "lemma": "draft",
    "pos": "N",
    "gloss": "preliminary version",
    "dewey": "808",
    "t1_decomposition": "VERSION(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "version",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2284,
    "lemma": "humans",
    "pos": "N",
    "gloss": "people",
    "dewey": "599",
    "t1_decomposition": "PEOPLE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "synonym",
        "target": "people",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 2285,
    "lemma": "hundreds",
    "pos": "N",
    "gloss": "large number",
    "dewey": "513",
    "t1_decomposition": "NUMBER(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2290,
    "lemma": "markets",
    "pos": "N",
    "gloss": "places for trade",
    "dewey": "381",
    "t1_decomposition": "PLACE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "place",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2291,
    "lemma": "medium",
    "pos": "N",
    "gloss": "intermediate",
    "dewey": "001",
    "t1_decomposition": "INTERMEDIATE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "intermediate",
        "weight": 0.95
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "assembly",
    "pos": "N",
    "gloss": "a group of people who come together for a common purpose or meeting",
    "dewey": "320",
    "t1_decomposition": "something and people and gather",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "gathering",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "breakfast",
    "pos": "N",
    "gloss": "the first meal of the day that people eat in the morning",
    "dewey": "641",
    "t1_decomposition": "meal and morning",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "meal",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "combination",
    "pos": "N",
    "gloss": "a mixture of different things that are put together to create something new",
    "dewey": "001",
    "t1_decomposition": "something and mix",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "mixture",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "customer",
    "pos": "N",
    "gloss": "a person who buys goods or services from a business or store",
    "dewey": "658",
    "t1_decomposition": "someone and buy",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "buyer",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "desire",
    "pos": "N",
    "gloss": "a strong feeling of wanting something or someone",
    "dewey": "152",
    "t1_decomposition": "want and something",
    "depth": 2,
    "edges": [
      {
        "rel": "synonym",
        "target": "wish",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "draft",
    "pos": "N",
    "gloss": "a preliminary version of a document or plan that is not yet final",
    "dewey": "808",
    "t1_decomposition": "version and not final",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "version",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "humans",
    "pos": "N",
    "gloss": "people who are alive and part of the human species",
    "dewey": "599",
    "t1_decomposition": "people",
    "depth": 2,
    "edges": [
      {
        "rel": "synonym",
        "target": "people",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "hundreds",
    "pos": "N",
    "gloss": "a large number of things or people that can be counted",
    "dewey": "513",
    "t1_decomposition": "many and something",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "markets",
    "pos": "N",
    "gloss": "places where people buy and sell goods or services",
    "dewey": "381",
    "t1_decomposition": "place and buy and sell",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "place",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "medium",
    "pos": "N",
    "gloss": "something that is in the middle or average in size, amount, or degree",
    "dewey": "001",
    "t1_decomposition": "something and middle",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "intermediate",
        "weight": 0.95
      }
    ]
  }
]
