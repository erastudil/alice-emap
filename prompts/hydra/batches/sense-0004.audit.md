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
["a-long-time", "a-short-time", "above", "after", "air", "all", "alternative", "animal", "audience", "awards", "back", "bad", "be", "be-somewhere", "bear", "because", "before", "below", "big", "blood", "body", "can", "clean", "clothes", "cold", "color", "creature", "cut", "dark", "dick", "die", "do", "dont-want", "drink", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "i", "if", "inside", "kind", "know", "labour", "land", "light", "like", "little", "live", "make", "maybe", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "plant", "pull", "push", "put", "round", "run", "same", "say", "see", "side", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "stone", "straight", "sun", "take", "teachers", "tech", "there-is", "think", "this", "touch", "trees", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "wood", "words", "you"]

INPUT:
[
  {
    "id": 1754,
    "lemma": "teachers",
    "pos": "N",
    "gloss": "persons who deliver instruction or educate students",
    "dewey": "371.1",
    "t1_decomposition": "AGENTS(x) & CAUSE(x, LEARN(y))",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "teacher",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "educator",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "education",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 1760,
    "lemma": "audience",
    "pos": "N",
    "gloss": "an assembled group of listeners or spectators",
    "dewey": "302.3",
    "t1_decomposition": "GROUP(HUMANS(x)) & PERCEIVE(x, PERFORMANCE(y))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "group",
        "weight": 0.9
      },
      {
        "rel": "has_member",
        "target": "spectator",
        "weight": 0.85
      },
      {
        "rel": "domain_topic",
        "target": "entertainment",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 1803,
    "lemma": "clothes",
    "pos": "N",
    "gloss": "items worn to cover the body",
    "dewey": "687",
    "t1_decomposition": "ARTIFACT(x) \u2227 COVER(x, BODY(y))",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "covering",
        "weight": 0.85
      },
      {
        "rel": "has_member",
        "target": "shirt",
        "weight": 0.8
      },
      {
        "rel": "has_member",
        "target": "trousers",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 1851,
    "lemma": "alternative",
    "pos": "N",
    "gloss": "one of two or more available possibilities",
    "dewey": "160",
    "t1_decomposition": "POSSIBILITY(x) & EXCLUSIVE_OR(x, y)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "option",
        "weight": 0.9
      },
      {
        "rel": "synonym",
        "target": "choice",
        "weight": 0.85
      },
      {
        "rel": "derivation",
        "target": "alternate",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 1854,
    "lemma": "awards",
    "pos": "N",
    "gloss": "marks of recognition given for achievement",
    "dewey": "001.44",
    "t1_decomposition": "PLUR(x) & RECOGNITION(x) & MERIT(y)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "award",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "honor",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 1855,
    "lemma": "bear",
    "pos": "N",
    "gloss": "large heavy mammal of the family Ursidae",
    "dewey": "599.78",
    "t1_decomposition": "MAMMAL(x) & URSID(x) & CLAWED(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "carnivore",
        "weight": 0.95
      },
      {
        "rel": "member_of",
        "target": "ursidae",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "zoology",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 1902,
    "lemma": "dick",
    "pos": "N",
    "gloss": "vulgar slang for a penis",
    "dewey": "611.65",
    "t1_decomposition": "ORGAN(x) \u2227 MALE_GENITALIA(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "penis",
        "weight": 0.95
      },
      {
        "rel": "synonym",
        "target": "cock",
        "weight": 0.85
      },
      {
        "rel": "part_of",
        "target": "body",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 1912,
    "lemma": "labour",
    "pos": "N",
    "gloss": "productive work, especially hard physical effort",
    "dewey": "331",
    "t1_decomposition": "EFFORT(x) \u2227 PRODUCE(x, VALUE)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "work",
        "weight": 0.95
      },
      {
        "rel": "synonym",
        "target": "labor",
        "weight": 0.95
      },
      {
        "rel": "derivation",
        "target": "laborer",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 1953,
    "lemma": "tech",
    "pos": "N",
    "gloss": "technology or technological equipment collectively",
    "dewey": "600",
    "t1_decomposition": "ARTIFACT(x) \u2227 APPLIED_SCIENCE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "technology",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "engineering",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 1954,
    "lemma": "trees",
    "pos": "N",
    "gloss": "plural of tree; woody perennial plants",
    "dewey": "582.16",
    "t1_decomposition": "PLURAL(x) \u2227 TREE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "tree",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "plant",
        "weight": 0.9
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "teachers",
    "pos": "N",
    "gloss": "people who teach or educate students in a school or other setting",
    "dewey": "371",
    "t1_decomposition": "someone(x) & teach(x, people(y))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "educator",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "education",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "audience",
    "pos": "N",
    "gloss": "a group of people who gather to listen or watch a performance or presentation",
    "dewey": "700",
    "t1_decomposition": "people(x) & listen(x, performance(y))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "group",
        "weight": 0.9
      },
      {
        "rel": "has_member",
        "target": "spectator",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "clothes",
    "pos": "N",
    "gloss": "items that people wear to cover their bodies",
    "dewey": "391",
    "t1_decomposition": "something(x) & wear(x, body(y))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "covering",
        "weight": 0.85
      },
      {
        "rel": "has_part",
        "target": "shirt",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "alternative",
    "pos": "N",
    "gloss": "one of several options or choices that are available",
    "dewey": "153",
    "t1_decomposition": "something(x) & choose(x, option(y))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "option",
        "weight": 0.9
      },
      {
        "rel": "synonym",
        "target": "choice",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "awards",
    "pos": "N",
    "gloss": "recognition or prizes given to people for their achievements",
    "dewey": "700",
    "t1_decomposition": "something(x) & give(x, people(y)) & recognize(y, achievement(z))",
    "depth": 3,
    "edges": [
      {
        "rel": "form_of",
        "target": "award",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "honor",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "bear",
    "pos": "N",
    "gloss": "a large and powerful animal that lives in the forest or woods",
    "dewey": "599",
    "t1_decomposition": "animal(x) & big(x) & strong(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "animal",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "forest",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "dick",
    "pos": "N",
    "gloss": "a vulgar term for a male genital organ",
    "dewey": "611",
    "t1_decomposition": "part(x) & body(x) & male(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "organ",
        "weight": 0.95
      },
      {
        "rel": "part_of",
        "target": "body",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "labour",
    "pos": "N",
    "gloss": "hard work or effort that people do to produce something",
    "dewey": "331",
    "t1_decomposition": "people(x) & work(x) & produce(x, something(y))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "work",
        "weight": 0.95
      },
      {
        "rel": "synonym",
        "target": "labor",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "tech",
    "pos": "N",
    "gloss": "technology or machines that are used to make things or solve problems",
    "dewey": "620",
    "t1_decomposition": "something(x) & make(x, things(y)) & use(x, machine(z))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "technology",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "engineering",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "trees",
    "pos": "N",
    "gloss": "tall plants with a single main stem and branches",
    "dewey": "582",
    "t1_decomposition": "something(x) & plant(x) & tall(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "form_of",
        "target": "tree",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "plant",
        "weight": 0.9
      }
    ]
  }
]
