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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "can", "clean", "cold", "color", "creature", "cut", "dark", "die", "do", "dont-want", "drink", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "fitness", "foot", "for-some-time", "francis", "friendship", "front", "gary", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "i", "idiot", "if", "inside", "keys", "kind", "know", "land", "lawyers", "lifetime", "light", "like", "little", "live", "make", "makeup", "maybe", "medal", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "plant", "pull", "push", "put", "round", "run", "same", "say", "see", "side", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "stone", "straight", "sun", "take", "there-is", "think", "this", "touch", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "wood", "words", "you"]

INPUT:
[
  {
    "id": 3466,
    "lemma": "fitness",
    "pos": "N",
    "gloss": "the condition of being physically fit",
    "dewey": "613.7",
    "t1_decomposition": "STATE(x) \u2227 PHYSICAL(x) \u2227 HEALTHY(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "health",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "cardiovascular fitness",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 3467,
    "lemma": "francis",
    "pos": "N",
    "gloss": "a male given name",
    "dewey": "929.4",
    "t1_decomposition": "NAME(x) \u2227 GENDER(x, male)",
    "depth": 5,
    "edges": [
      {
        "rel": "instance_of",
        "target": "name",
        "weight": 0.95
      },
      {
        "rel": "has_instance",
        "target": "pope francis",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 3468,
    "lemma": "friendship",
    "pos": "N",
    "gloss": "a relationship between friends",
    "dewey": "177",
    "t1_decomposition": "RELATION(x) \u2227 BETWEEN(x, friend, friend)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "relationship",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "best friendship",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 3469,
    "lemma": "gary",
    "pos": "N",
    "gloss": "a male given name",
    "dewey": "929.4",
    "t1_decomposition": "NAME(x) \u2227 GENDER(x, male)",
    "depth": 5,
    "edges": [
      {
        "rel": "instance_of",
        "target": "name",
        "weight": 0.95
      },
      {
        "rel": "has_instance",
        "target": "gary cooper",
        "weight": 0.6
      }
    ]
  },
  {
    "id": 3471,
    "lemma": "idiot",
    "pos": "N",
    "gloss": "a person of low intelligence",
    "dewey": "153.9",
    "t1_decomposition": "HUMAN(x) \u2227 INTELLIGENCE(x, low)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "fool",
        "weight": 0.9
      },
      {
        "rel": "antonym",
        "target": "genius",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 3473,
    "lemma": "keys",
    "pos": "N",
    "gloss": "small metal instruments for opening locks",
    "dewey": "683",
    "t1_decomposition": "OBJECT(x) \u2227 MATERIAL(x, metal) \u2227 PURPOSE(x, OPEN(y))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "tool",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "car key",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 3474,
    "lemma": "lawyers",
    "pos": "N",
    "gloss": "professionals who practice law",
    "dewey": "340",
    "t1_decomposition": "HUMAN(x) \u2227 PROFESSION(x, lawyer)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "professional",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "attorney",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 3475,
    "lemma": "lifetime",
    "pos": "N",
    "gloss": "the duration of a person's life",
    "dewey": "304",
    "t1_decomposition": "DURATION(x) \u2227 OF(x, LIFE(y))",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "period",
        "weight": 0.9
      },
      {
        "rel": "part_of",
        "target": "biography",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 3477,
    "lemma": "makeup",
    "pos": "N",
    "gloss": "cosmetics applied to the face",
    "dewey": "646",
    "t1_decomposition": "SUBSTANCE(x) \u2227 PURPOSE(x, APPLY(y, face))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "cosmetic",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "lipstick",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 3478,
    "lemma": "medal",
    "pos": "N",
    "gloss": "a metal disc awarded as an honor",
    "dewey": "737",
    "t1_decomposition": "OBJECT(x) \u2227 MATERIAL(x, metal) \u2227 PURPOSE(x, AWARD(y))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "award",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "gold medal",
        "weight": 0.8
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "fitness",
    "pos": "N",
    "gloss": "the state of being physically healthy and strong",
    "dewey": "613.7",
    "t1_decomposition": "STATE(x) \u2227 PHYSICAL(x) \u2227 HEALTHY(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "health",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "physical fitness",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "francis",
    "pos": "N",
    "gloss": "a male given name often associated with a person who is kind and gentle",
    "dewey": "929.4",
    "t1_decomposition": "someone \u2227 NAME(x)",
    "depth": 5,
    "edges": [
      {
        "rel": "instance_of",
        "target": "name",
        "weight": 0.95
      },
      {
        "rel": "has_instance",
        "target": "pope francis",
        "weight": 0.7
      }
    ]
  },
  {
    "lemma": "friendship",
    "pos": "N",
    "gloss": "a close and supportive relationship between two people who care about each other",
    "dewey": "177",
    "t1_decomposition": "RELATION(x) \u2227 BETWEEN(x, someone, someone)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "relationship",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "close friendship",
        "weight": 0.7
      }
    ]
  },
  {
    "lemma": "gary",
    "pos": "N",
    "gloss": "a male given name often associated with a person who is strong and confident",
    "dewey": "929.4",
    "t1_decomposition": "someone \u2227 NAME(x)",
    "depth": 5,
    "edges": [
      {
        "rel": "instance_of",
        "target": "name",
        "weight": 0.95
      },
      {
        "rel": "has_instance",
        "target": "gary cooper",
        "weight": 0.6
      }
    ]
  },
  {
    "lemma": "idiot",
    "pos": "N",
    "gloss": "a person who is not very intelligent or wise and often does foolish things",
    "dewey": "153.9",
    "t1_decomposition": "someone \u2227 INTELLIGENCE(x, low)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "fool",
        "weight": 0.9
      },
      {
        "rel": "antonym",
        "target": "genius",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "keys",
    "pos": "N",
    "gloss": "small objects used to open locks and gain access to something",
    "dewey": "683",
    "t1_decomposition": "something \u2227 PURPOSE(x, OPEN(y))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "tool",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "car key",
        "weight": 0.7
      }
    ]
  },
  {
    "lemma": "lawyers",
    "pos": "N",
    "gloss": "people who practice law and help others with legal issues",
    "dewey": "340",
    "t1_decomposition": "someone \u2227 PROFESSION(x, lawyer)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "professional",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "attorney",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "lifetime",
    "pos": "N",
    "gloss": "the length of time that a person is alive and experiences different things",
    "dewey": "304",
    "t1_decomposition": "DURATION(x) \u2227 OF(x, LIFE(y))",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "period",
        "weight": 0.9
      },
      {
        "rel": "part_of",
        "target": "biography",
        "weight": 0.7
      }
    ]
  },
  {
    "lemma": "makeup",
    "pos": "N",
    "gloss": "cosmetics applied to the face to enhance or change one's appearance",
    "dewey": "646",
    "t1_decomposition": "something \u2227 PURPOSE(x, APPLY(y, face))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "cosmetic",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "lipstick",
        "weight": 0.7
      }
    ]
  },
  {
    "lemma": "medal",
    "pos": "N",
    "gloss": "a small metal object awarded to someone as a symbol of achievement or honor",
    "dewey": "737",
    "t1_decomposition": "something \u2227 PURPOSE(x, AWARD(y))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "award",
        "weight": 0.95
      },
      {
        "rel": "hyponym",
        "target": "gold medal",
        "weight": 0.8
      }
    ]
  }
]
