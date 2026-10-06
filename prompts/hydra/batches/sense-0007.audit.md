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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "can", "clean", "clock", "cold", "color", "cooking", "creature", "cut", "dark", "die", "do", "dont-want", "drink", "drinks", "ear", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "i", "if", "inside", "kind", "know", "land", "light", "like", "little", "live", "make", "maybe", "mine", "moment", "more", "move", "much", "mum", "near", "not", "now", "one", "open", "opinions", "other", "part", "patterns", "people", "plant", "presents", "pull", "push", "put", "round", "run", "same", "say", "see", "side", "sit", "skill", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "stomach", "stone", "straight", "sun", "take", "there-is", "think", "this", "touch", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "wood", "words", "you"]

INPUT:
[
  {
    "id": 3081,
    "lemma": "cooking",
    "pos": "N",
    "gloss": "the process of preparing food",
    "dewey": "641.5",
    "t1_decomposition": "PROCESS(x) \u2227 PREPARE(x, FOOD)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "process",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "baking",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 3200,
    "lemma": "clock",
    "pos": "N",
    "gloss": "an instrument for measuring and indicating time",
    "dewey": "681.113",
    "t1_decomposition": "INSTRUMENT(x) ^ MEASURE(x, TIME)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "timepiece",
        "weight": 0.95
      },
      {
        "rel": "has_part",
        "target": "dial",
        "weight": 0.8
      },
      {
        "rel": "instrument_of",
        "target": "chronometry",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 3210,
    "lemma": "drinks",
    "pos": "N",
    "gloss": "plural of drink; liquids intended for ingestion",
    "dewey": "641.87",
    "t1_decomposition": "PLURAL(x) ^ LIQUID(x) ^ INGESTIBLE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "drink",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "beverage",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 3211,
    "lemma": "ear",
    "pos": "N",
    "gloss": "the vertebrate organ of hearing and balance",
    "dewey": "611.85",
    "t1_decomposition": "ORGAN(x) ^ SENSE_HEARING(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organ",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "head",
        "weight": 0.9
      },
      {
        "rel": "has_part",
        "target": "tympanum",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 3303,
    "lemma": "skill",
    "pos": "N",
    "gloss": "the ability to do something well; expertise",
    "dewey": "153.9",
    "t1_decomposition": "ABILITY(x, PROFICIENT)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "ability",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "craft",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 3306,
    "lemma": "stomach",
    "pos": "N",
    "gloss": "internal organ where digestion begins",
    "dewey": "612.3",
    "t1_decomposition": "ORGAN(x) & DIGESTIVE(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organ",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "digestive system",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 3350,
    "lemma": "mum",
    "pos": "N",
    "gloss": "one's mother (British informal)",
    "dewey": "392",
    "t1_decomposition": "PERSON(x) & MOTHER(x, y)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "mother",
        "weight": 0.95
      },
      {
        "rel": "synonym",
        "target": "mom",
        "weight": 0.9
      },
      {
        "rel": "synonym",
        "target": "mama",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 3351,
    "lemma": "opinions",
    "pos": "N",
    "gloss": "personal beliefs or judgments about matters",
    "dewey": "121",
    "t1_decomposition": "PLURAL(BELIEF(x))",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "opinion",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "belief",
        "weight": 0.85
      },
      {
        "rel": "antonym",
        "target": "facts",
        "weight": 0.6
      }
    ]
  },
  {
    "id": 3352,
    "lemma": "patterns",
    "pos": "N",
    "gloss": "repeated decorative designs or regular arrangements",
    "dewey": "745",
    "t1_decomposition": "PLURAL(DESIGN(x)) & REGULAR(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "pattern",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "design",
        "weight": 0.8
      },
      {
        "rel": "synonym",
        "target": "motifs",
        "weight": 0.7
      }
    ]
  },
  {
    "id": 3353,
    "lemma": "presents",
    "pos": "N",
    "gloss": "things given voluntarily without payment",
    "dewey": "394",
    "t1_decomposition": "PLURAL(GIFT(x))",
    "depth": 4,
    "edges": [
      {
        "rel": "form_of",
        "target": "present",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "gift",
        "weight": 0.9
      },
      {
        "rel": "synonym",
        "target": "gifts",
        "weight": 0.85
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "cooking",
    "pos": "N",
    "gloss": "the process of preparing food for people to eat",
    "dewey": "641",
    "t1_decomposition": "make(something) and eat(something)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "preparing",
        "weight": 0.8
      },
      {
        "rel": "hyponym",
        "target": "baking",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "clock",
    "pos": "N",
    "gloss": "an instrument that shows people the time of day",
    "dewey": "681.1",
    "t1_decomposition": "instrument(x) and show(x, time)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "timepiece",
        "weight": 0.95
      },
      {
        "rel": "has_part",
        "target": "hand",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "drinks",
    "pos": "N",
    "gloss": "liquids that people drink to satisfy their thirst",
    "dewey": "641.2",
    "t1_decomposition": "something and drink(something)",
    "depth": 2,
    "edges": [
      {
        "rel": "form_of",
        "target": "drink",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "beverage",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "ear",
    "pos": "N",
    "gloss": "the part of the body that people use to hear sounds",
    "dewey": "611",
    "t1_decomposition": "part(x) and hear(something)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organ",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "head",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "skill",
    "pos": "N",
    "gloss": "the ability that people have to do something well",
    "dewey": "153",
    "t1_decomposition": "can(x) and do(something) and good(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "ability",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "craft",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "stomach",
    "pos": "N",
    "gloss": "the part of the body where food goes after people eat",
    "dewey": "612",
    "t1_decomposition": "part(x) and eat(something) and inside(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organ",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "body",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "mum",
    "pos": "N",
    "gloss": "a woman who is the mother of someone",
    "dewey": "306.85",
    "t1_decomposition": "someone and mother(someone)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "mother",
        "weight": 0.95
      },
      {
        "rel": "synonym",
        "target": "mom",
        "weight": 0.9
      }
    ]
  },
  {
    "lemma": "opinions",
    "pos": "N",
    "gloss": "the beliefs or thoughts that people have about something",
    "dewey": "121",
    "t1_decomposition": "someone and think(something)",
    "depth": 2,
    "edges": [
      {
        "rel": "form_of",
        "target": "opinion",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "belief",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "patterns",
    "pos": "N",
    "gloss": "the regular arrangements of things that people see or make",
    "dewey": "745",
    "t1_decomposition": "something and see(something) and regular(something)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "pattern",
        "weight": 0.95
      },
      {
        "rel": "hypernym",
        "target": "design",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "presents",
    "pos": "N",
    "gloss": "the things that people give to someone as a gift",
    "dewey": "394",
    "t1_decomposition": "something and give(something) and someone",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "present",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "gift",
        "weight": 0.9
      }
    ]
  }
]
