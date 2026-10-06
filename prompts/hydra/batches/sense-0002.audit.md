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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "business", "can", "city", "clean", "cold", "color", "creature", "cut", "dark", "die", "do", "dont-want", "drink", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "house", "i", "if", "inside", "kind", "know", "land", "light", "like", "little", "live", "make", "maybe", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "person", "place", "plant", "pull", "push", "put", "round", "run", "same", "say", "see", "side", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "state", "stone", "straight", "sun", "take", "there-is", "thing", "think", "this", "three", "touch", "true", "two", "very", "walk", "want", "warm", "water", "week", "when", "where", "women", "wood", "words", "you"]

INPUT:
[
  {
    "id": 207,
    "lemma": "state",
    "pos": "N",
    "gloss": "the condition of a system or entity",
    "dewey": "120",
    "t1_decomposition": "STATE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "condition",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 208,
    "lemma": "three",
    "pos": "N",
    "gloss": "the number 3",
    "dewey": "510",
    "t1_decomposition": "NUMBER(x, 3)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.96
      }
    ]
  },
  {
    "id": 225,
    "lemma": "thing",
    "pos": "N",
    "gloss": "an inanimate material object or distinct entity",
    "dewey": "110",
    "t1_decomposition": "ENTITY(x) & ~ANIMATE(x)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "entity",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "object",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "artifact",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 226,
    "lemma": "house",
    "pos": "N",
    "gloss": "a building designed for human habitation",
    "dewey": "728",
    "t1_decomposition": "BUILDING(x) & CAUSE(x, SHELTER(y)) & HUMAN(y)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "building",
        "weight": 0.95
      },
      {
        "rel": "has_part",
        "target": "roof",
        "weight": 0.9
      },
      {
        "rel": "has_part",
        "target": "room",
        "weight": 0.9
      },
      {
        "rel": "bridge_function",
        "target": "dwell",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 227,
    "lemma": "place",
    "pos": "N",
    "gloss": "a particular portion of space, location, or area",
    "dewey": "910",
    "t1_decomposition": "LOCATION(x)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "spatial_entity",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "area",
        "weight": 0.85
      },
      {
        "rel": "hyponym",
        "target": "point",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 250,
    "lemma": "city",
    "pos": "N",
    "gloss": "a large human settlement",
    "dewey": "307.76",
    "t1_decomposition": "CITY(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "human settlement",
        "weight": 0.93
      }
    ]
  },
  {
    "id": 276,
    "lemma": "women",
    "pos": "N",
    "gloss": "adult human females",
    "dewey": "305.4",
    "t1_decomposition": "\u03bbx. PLURAL(x) \u2227 ADULT(x) \u2227 HUMAN(x) \u2227 FEMALE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "woman",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "person",
        "weight": 0.9
      },
      {
        "rel": "antonym",
        "target": "men",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 277,
    "lemma": "business",
    "pos": "N",
    "gloss": "commercial or industrial enterprise or activity",
    "dewey": "650",
    "t1_decomposition": "\u03bbx. ACTIVITY(x) \u2227 COMMERCE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "enterprise",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "commerce",
        "weight": 0.85
      },
      {
        "rel": "derivation",
        "target": "busy",
        "weight": 0.6
      }
    ]
  },
  {
    "id": 282,
    "lemma": "week",
    "pos": "N",
    "gloss": "a standard period of seven consecutive days",
    "dewey": "529",
    "t1_decomposition": "\u03bbt. DURATION(t, 7 * DAY)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "period",
        "weight": 0.85
      },
      {
        "rel": "part_of",
        "target": "month",
        "weight": 0.8
      },
      {
        "rel": "has_part",
        "target": "day",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 287,
    "lemma": "person",
    "pos": "N",
    "gloss": "an individual human being",
    "dewey": "301",
    "t1_decomposition": "\u03bbx. HUMAN(x) \u2227 INDIVIDUAL(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organism",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "woman",
        "weight": 0.85
      },
      {
        "rel": "hyponym",
        "target": "man",
        "weight": 0.85
      },
      {
        "rel": "derivation",
        "target": "personal",
        "weight": 0.75
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "state",
    "pos": "N",
    "gloss": "a particular condition or status of something or someone",
    "dewey": "120",
    "t1_decomposition": "CONDITION(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "condition",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "three",
    "pos": "N",
    "gloss": "the number that comes after two and before four",
    "dewey": "510",
    "t1_decomposition": "NUMBER(x) & ONE(x) & ONE(x) & ONE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.96
      }
    ]
  },
  {
    "lemma": "thing",
    "pos": "N",
    "gloss": "an object or entity that exists or is perceived",
    "dewey": "110",
    "t1_decomposition": "SOMETHING(x)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "entity",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "object",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "house",
    "pos": "N",
    "gloss": "a building that serves as a dwelling or shelter for people",
    "dewey": "728",
    "t1_decomposition": "BUILDING(x) & BE_SOMEWHERE(x, PEOPLE(y))",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "building",
        "weight": 0.95
      },
      {
        "rel": "has_part",
        "target": "room",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "place",
    "pos": "N",
    "gloss": "a particular location or area where something exists or happens",
    "dewey": "910",
    "t1_decomposition": "WHERE(x)",
    "depth": 1,
    "edges": [
      {
        "rel": "hypernym",
        "target": "location",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "area",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "city",
    "pos": "N",
    "gloss": "a large and permanent human settlement",
    "dewey": "307.76",
    "t1_decomposition": "PLACE(x) & MANY(PEOPLE(y)) & BE_SOMEWHERE(y, x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "settlement",
        "weight": 0.93
      }
    ]
  },
  {
    "lemma": "women",
    "pos": "N",
    "gloss": "adult human females",
    "dewey": "305.4",
    "t1_decomposition": "SOMEONE(x) & FEMALE(x) & ADULT(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "woman",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "person",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "business",
    "pos": "N",
    "gloss": "an activity or enterprise that is done to earn money",
    "dewey": "650",
    "t1_decomposition": "ACTIVITY(x) & DO(x, PEOPLE(y)) & WANT(y, MONEY(z))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "enterprise",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "commerce",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "week",
    "pos": "N",
    "gloss": "a period of seven consecutive days",
    "dewey": "529",
    "t1_decomposition": "SOME(x) & DAY(x) & SEVEN(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "period",
        "weight": 0.85
      },
      {
        "rel": "has_part",
        "target": "day",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "person",
    "pos": "N",
    "gloss": "an individual human being",
    "dewey": "301",
    "t1_decomposition": "SOMEONE(x) & HUMAN(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organism",
        "weight": 0.8
      }
    ]
  }
]
