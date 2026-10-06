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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "audio", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "can", "clean", "cold", "color", "creature", "cut", "dark", "davis", "die", "do", "dont-want", "drink", "earth", "eat", "end", "eric", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "i", "if", "inside", "islands", "kind", "know", "land", "light", "like", "little", "live", "make", "maybe", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "plant", "pull", "push", "put", "railway", "round", "run", "same", "say", "see", "shock", "side", "silence", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "soldier", "some", "someone", "something", "sound", "stand", "stone", "straight", "sun", "supporters", "take", "there-is", "think", "this", "tons", "touch", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "wood", "words", "you"]

INPUT:
[
  {
    "id": 2811,
    "lemma": "islands",
    "pos": "N",
    "gloss": "tracts of land completely surrounded by water",
    "dewey": "551.42",
    "t1_decomposition": "\u03bbx.PLURAL(LANDMASS(x)) \u2227 SURROUNDED_BY(x, WATER)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "island",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "landmass",
        "weight": 0.9
      },
      {
        "rel": "member_of",
        "target": "archipelago",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 2857,
    "lemma": "davis",
    "pos": "N",
    "gloss": "common Anglo-Welsh surname or place name",
    "dewey": "929.4",
    "t1_decomposition": "NAME(x, PROPER(x))",
    "depth": 2,
    "edges": [
      {
        "rel": "instance_of",
        "target": "surname",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2860,
    "lemma": "eric",
    "pos": "N",
    "gloss": "masculine given name of Old Norse origin",
    "dewey": "929.4",
    "t1_decomposition": "NAME(x, MALE(x))",
    "depth": 2,
    "edges": [
      {
        "rel": "instance_of",
        "target": "given_name",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2950,
    "lemma": "audio",
    "pos": "N",
    "gloss": "sound, especially when recorded, transmitted, or reproduced",
    "dewey": "621.389",
    "t1_decomposition": "SOUND(x) & TRANSMITTED(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "sound",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "electronics",
        "weight": 0.85
      },
      {
        "rel": "bridge_function",
        "target": "speaker",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 3051,
    "lemma": "railway",
    "pos": "N",
    "gloss": "a track for trains",
    "dewey": "625.1",
    "t1_decomposition": "TRACK(x) \u2227 FOR(x, TRAIN)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "transportation",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "subway",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 3056,
    "lemma": "shock",
    "pos": "N",
    "gloss": "a sudden upsetting or surprising event",
    "dewey": "152.4",
    "t1_decomposition": "EVENT(x) \u2227 SUDDEN(x) \u2227 UPSETTING(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "surprise",
        "weight": 0.9
      },
      {
        "rel": "causes",
        "target": "fear",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 3057,
    "lemma": "silence",
    "pos": "N",
    "gloss": "absence of sound",
    "dewey": "152.1",
    "t1_decomposition": "ABSENCE(x, SOUND)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "quiet",
        "weight": 0.9
      },
      {
        "rel": "antonym",
        "target": "noise",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 3058,
    "lemma": "soldier",
    "pos": "N",
    "gloss": "a member of an army",
    "dewey": "355.1",
    "t1_decomposition": "PERSON(x) \u2227 MEMBER(x, ARMY)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "military personnel",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "infantryman",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 3060,
    "lemma": "supporters",
    "pos": "N",
    "gloss": "people who support a cause or person",
    "dewey": "303.3",
    "t1_decomposition": "PEOPLE(x) \u2227 SUPPORT(x, y)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "people",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "fans",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 3063,
    "lemma": "tons",
    "pos": "N",
    "gloss": "a large amount",
    "dewey": "530.8",
    "t1_decomposition": "AMOUNT(x) \u2227 LARGE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "loads",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "quantity",
        "weight": 0.8
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "islands",
    "pos": "N",
    "gloss": "pieces of land that are surrounded by water on all sides",
    "dewey": "551.42",
    "t1_decomposition": "something(x) & water(y) & there-is(z, x, y) & surrounded(x, y)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "island",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "land",
        "weight": 0.9
      },
      {
        "rel": "part_of",
        "target": "archipelago",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "davis",
    "pos": "N",
    "gloss": "a common surname of Welsh origin given to people",
    "dewey": "929.4",
    "t1_decomposition": "someone(x) & name(x, davis)",
    "depth": 2,
    "edges": [
      {
        "rel": "instance_of",
        "target": "surname",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "eric",
    "pos": "N",
    "gloss": "a masculine given name of Old Norse origin given to people",
    "dewey": "929.4",
    "t1_decomposition": "someone(x) & name(x, eric)",
    "depth": 2,
    "edges": [
      {
        "rel": "instance_of",
        "target": "given_name",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "audio",
    "pos": "N",
    "gloss": "sounds that are recorded or transmitted through devices",
    "dewey": "621.389",
    "t1_decomposition": "sound(x) & something(y) & do(y, x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "sound",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "electronics",
        "weight": 0.85
      },
      {
        "rel": "bridge_function",
        "target": "speaker",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "railway",
    "pos": "N",
    "gloss": "a path or track where trains can move from one place to another",
    "dewey": "625.1",
    "t1_decomposition": "something(x) & part(x, train) & move(x, y)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "transportation",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "subway",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "shock",
    "pos": "N",
    "gloss": "a sudden and upsetting event that can cause people to feel fear or surprise",
    "dewey": "152.4",
    "t1_decomposition": "event(x) & sudden(x) & people(y) & feel(y, x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "surprise",
        "weight": 0.9
      },
      {
        "rel": "causes",
        "target": "fear",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "silence",
    "pos": "N",
    "gloss": "the absence of sound or noise in a place or situation",
    "dewey": "152.1",
    "t1_decomposition": "not(something(x)) & sound(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "quiet",
        "weight": 0.9
      },
      {
        "rel": "antonym",
        "target": "noise",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "soldier",
    "pos": "N",
    "gloss": "a person who serves in an army or military organization",
    "dewey": "355.1",
    "t1_decomposition": "someone(x) & part(x, army)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "military personnel",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "infantryman",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "supporters",
    "pos": "N",
    "gloss": "people who give help or approval to a person, group, or cause",
    "dewey": "303.3",
    "t1_decomposition": "people(x) & do(x, help)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "people",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "fans",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "tons",
    "pos": "N",
    "gloss": "a very large quantity or amount of something",
    "dewey": "530.8",
    "t1_decomposition": "something(x) & much(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "loads",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "quantity",
        "weight": 0.8
      }
    ]
  }
]
