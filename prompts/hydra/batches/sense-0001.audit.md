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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "can", "clean", "cold", "color", "creature", "cut", "dark", "die", "do", "dont-want", "drink", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "i", "if", "inside", "kind", "know", "land", "light", "like", "little", "live", "make", "maybe", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "plant", "pull", "push", "put", "round", "run", "same", "say", "see", "side", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "stone", "straight", "sun", "take", "there-is", "think", "this", "touch", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "wood", "words", "you", "\u03b6"]

INPUT:
[
  {
    "id": 0,
    "lemma": "\u03b6",
    "pos": "N",
    "gloss": "lambda",
    "dewey": "510",
    "t1_decomposition": "MATHEMATICAL(x)",
    "depth": 0,
    "edges": [
      {
        "rel": "hypernym",
        "target": "target_lemma",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "entity",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "liquid",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "...",
        "weight": 0.9
      },
      {
        "rel": "attribute_of",
        "target": "provider",
        "weight": 0.9
      },
      {
        "rel": "has_instance",
        "target": "food",
        "weight": 0.8
      },
      {
        "rel": "entails",
        "target": "food",
        "weight": 0.7
      },
      {
        "rel": "hypernym",
        "target": "jeps",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "oklahoma sooners",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "university of oklahoma",
        "weight": 0.85
      },
      {
        "rel": "hypernym",
        "target": "oklahoma athletic teams",
        "weight": 0.75
      },
      {
        "rel": "instance_of",
        "target": "sports team",
        "weight": 0.6
      },
      {
        "rel": "part_of",
        "target": "university of oklahoma",
        "weight": 0.55
      },
      {
        "rel": "has_member",
        "target": "sooner",
        "weight": 0.5
      },
      {
        "rel": "synonym",
        "target": "university of oklahoma",
        "weight": 0.2
      },
      {
        "rel": "synonym",
        "target": "oklahoma athletic teams",
        "weight": 0.15
      },
      {
        "rel": "synonym",
        "target": "sooner",
        "weight": 0.1
      },
      {
        "rel": "synonym",
        "target": "oklahoma sooners",
        "weight": 0.05
      }
    ]
  },
  {
    "id": 2,
    "lemma": "people",
    "pos": "N",
    "gloss": "human beings collectively",
    "dewey": "305",
    "t1_decomposition": "GROUP(x) \u2227 HUMAN(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "group",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "population",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 5,
    "lemma": "body",
    "pos": "N",
    "gloss": "physical structure of a person or animal",
    "dewey": "611",
    "t1_decomposition": "PHYSICAL(x) \u2227 ORGANISM(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organism",
        "weight": 0.8
      },
      {
        "rel": "has_part",
        "target": "organ",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 6,
    "lemma": "kind",
    "pos": "N",
    "gloss": "a category of things having common characteristics",
    "dewey": "001",
    "t1_decomposition": "CATEGORY(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "category",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "type",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 7,
    "lemma": "part",
    "pos": "N",
    "gloss": "a portion or division of a whole",
    "dewey": "001",
    "t1_decomposition": "PORTION(x) \u2227 PART_OF(x,y)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "portion",
        "weight": 0.9
      },
      {
        "rel": "antonym",
        "target": "whole",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 11,
    "lemma": "one",
    "pos": "N",
    "gloss": "the number 1",
    "dewey": "513",
    "t1_decomposition": "NUMBER(x) \u2227 VALUE(x,1)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "unit",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 12,
    "lemma": "two",
    "pos": "N",
    "gloss": "the number 2",
    "dewey": "513",
    "t1_decomposition": "NUMBER(x) \u2227 VALUE(x,2)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "pair",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 29,
    "lemma": "words",
    "pos": "N",
    "gloss": "units of language with meaning",
    "dewey": "410",
    "t1_decomposition": "LINGUISTIC_UNIT(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "language",
        "weight": 0.8
      },
      {
        "rel": "part_of",
        "target": "sentence",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 48,
    "lemma": "moment",
    "pos": "N",
    "gloss": "very brief period of time",
    "dewey": "115",
    "t1_decomposition": "TIME(x) \u2227 SHORT(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "time",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "a-short-time",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 78,
    "lemma": "foot",
    "pos": "N",
    "gloss": "terminal weight-bearing part of the vertebrate leg",
    "dewey": "611.98",
    "t1_decomposition": "TERMINAL_PART(LEG(x)) & LOCOMOTIVE_BASE(x)",
    "depth": 5,
    "edges": [
      {
        "rel": "hypernym",
        "target": "extremity",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "leg",
        "weight": 0.98
      },
      {
        "rel": "has_part",
        "target": "toe",
        "weight": 0.95
      },
      {
        "rel": "instrument_of",
        "target": "walk",
        "weight": 0.92
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "\u03b6",
    "pos": "N",
    "gloss": "the eleventh letter of the Greek alphabet used in mathematics and science to represent various concepts",
    "dewey": "510",
    "t1_decomposition": "something(x) & symbol(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "symbol",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "people",
    "pos": "N",
    "gloss": "human beings collectively",
    "dewey": "300",
    "t1_decomposition": "group(someone)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "group",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "body",
    "pos": "N",
    "gloss": "physical structure of a person or animal",
    "dewey": "610",
    "t1_decomposition": "part(something) & physical(something)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organism",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "kind",
    "pos": "N",
    "gloss": "a category of things having common characteristics",
    "dewey": "001",
    "t1_decomposition": "category(something)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "category",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "part",
    "pos": "N",
    "gloss": "a portion or division of a whole",
    "dewey": "001",
    "t1_decomposition": "part(something)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "portion",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "one",
    "pos": "N",
    "gloss": "the number 1",
    "dewey": "510",
    "t1_decomposition": "number(one)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "two",
    "pos": "N",
    "gloss": "the number 2",
    "dewey": "510",
    "t1_decomposition": "number(two)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "words",
    "pos": "N",
    "gloss": "units of language with meaning",
    "dewey": "400",
    "t1_decomposition": "something(words)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "language",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "moment",
    "pos": "N",
    "gloss": "very brief period of time",
    "dewey": "115",
    "t1_decomposition": "time(moment) & short(moment)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "time",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "foot",
    "pos": "N",
    "gloss": "terminal weight-bearing part of the vertebrate leg",
    "dewey": "611",
    "t1_decomposition": "part(body) & part(leg)",
    "depth": 3,
    "edges": [
      {
        "rel": "part_of",
        "target": "leg",
        "weight": 0.98
      }
    ]
  }
]
