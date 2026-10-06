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
["a-long-time", "a-short-time", "above", "after", "air", "all", "animal", "back", "bad", "be", "be-somewhere", "because", "before", "below", "big", "blood", "body", "can", "clean", "cold", "color", "creature", "cut", "dark", "die", "do", "dont-want", "drink", "earth", "eat", "end", "eye", "face", "fall", "far", "fast", "feel", "fire", "foot", "for-some-time", "front", "give", "good", "grow", "hand", "happen", "hard", "head", "hear", "heavy", "here", "hold", "home", "hotel", "i", "if", "inside", "judge", "kind", "know", "lake", "land", "letter", "light", "like", "little", "live", "make", "material", "maybe", "mine", "moment", "more", "move", "much", "near", "not", "now", "one", "open", "other", "part", "people", "photos", "planning", "plant", "professor", "pull", "push", "put", "round", "run", "same", "say", "see", "showing", "side", "sit", "sky", "sleep", "slow", "small", "smell", "soft", "some", "someone", "something", "sound", "stand", "stone", "straight", "sun", "take", "there-is", "think", "this", "touch", "true", "two", "very", "walk", "want", "warm", "water", "when", "where", "william", "wood", "words", "you"]

INPUT:
[
  {
    "id": 1104,
    "lemma": "hotel",
    "pos": "N",
    "gloss": "commercial establishment offering paid lodging and services",
    "dewey": "647.94",
    "t1_decomposition": "\u03bbx.BUILDING(x) \u2227 PROVIDE(x, TEMPORARY_LODGING)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "building",
        "weight": 0.92
      },
      {
        "rel": "hyponym",
        "target": "motel",
        "weight": 0.85
      },
      {
        "rel": "has_part",
        "target": "room",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 1106,
    "lemma": "judge",
    "pos": "N",
    "gloss": "public official authorized to decide legal cases",
    "dewey": "347.014",
    "t1_decomposition": "\u03bbx.PERSON(x) \u2227 ADJUDICATE(x, LEGAL_CASE)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "official",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "law",
        "weight": 0.95
      },
      {
        "rel": "agent_of",
        "target": "adjudicate",
        "weight": 0.88
      }
    ]
  },
  {
    "id": 1109,
    "lemma": "letter",
    "pos": "N",
    "gloss": "written, typed, or printed postal communication",
    "dewey": "383.14",
    "t1_decomposition": "\u03bbx.DOCUMENT(x) \u2227 SENT_TO(x, RECIPIENT)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "document",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "epistle",
        "weight": 0.78
      },
      {
        "rel": "domain_topic",
        "target": "postal_system",
        "weight": 0.82
      }
    ]
  },
  {
    "id": 1111,
    "lemma": "material",
    "pos": "N",
    "gloss": "substance from which things can be constructed",
    "dewey": "620.11",
    "t1_decomposition": "\u03bbx.PHYSICAL_SUBSTANCE(x) \u2227 USE_FOR_MAKING(x, y)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "substance",
        "weight": 0.94
      },
      {
        "rel": "hyponym",
        "target": "fabric",
        "weight": 0.82
      },
      {
        "rel": "hyponym",
        "target": "metal",
        "weight": 0.84
      }
    ]
  },
  {
    "id": 1253,
    "lemma": "planning",
    "pos": "N",
    "gloss": "the process of making plans for something",
    "dewey": "658.4012",
    "t1_decomposition": "\u03bbx.(PROCESS(x) \u2227 FOR_FORMULATING_PLANS(x))",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "process",
        "weight": 0.9
      },
      {
        "rel": "derivation",
        "target": "plan",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "management",
        "weight": 0.8
      }
    ]
  },
  {
    "id": 1254,
    "lemma": "professor",
    "pos": "N",
    "gloss": "a university academic of the highest rank",
    "dewey": "378.12",
    "t1_decomposition": "\u03bbx.(EDUCATOR(x) \u2227 APPOINTED_AT_UNIVERSITY(x))",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "educator",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "academic",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "academia",
        "weight": 0.85
      }
    ]
  },
  {
    "id": 1306,
    "lemma": "showing",
    "pos": "N",
    "gloss": "an exhibition, display, or presentation of something",
    "dewey": "791.43",
    "t1_decomposition": "EVENT(e) & PRESENT(x, y)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "presentation",
        "weight": 0.85
      },
      {
        "rel": "derivation",
        "target": "show",
        "weight": 0.9
      },
      {
        "rel": "synonym",
        "target": "screening",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 1311,
    "lemma": "william",
    "pos": "N",
    "gloss": "a masculine given name of Germanic origin",
    "dewey": "929.44",
    "t1_decomposition": "NAME(x) & MASCULINE(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "name",
        "weight": 0.95
      },
      {
        "rel": "instance_of",
        "target": "given_name",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 1456,
    "lemma": "lake",
    "pos": "N",
    "gloss": "a large inland body of standing water",
    "dewey": "551.482",
    "t1_decomposition": "BODY_OF_WATER(x) & INLAND(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "waterbody",
        "weight": 0.95
      },
      {
        "rel": "substance_of",
        "target": "water",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "pond",
        "weight": 0.75
      }
    ]
  },
  {
    "id": 1463,
    "lemma": "photos",
    "pos": "N",
    "gloss": "plural images produced by photography",
    "dewey": "770",
    "t1_decomposition": "IMAGE(x) & PRODUCED_BY(x, LIGHT)",
    "depth": 4,
    "edges": [
      {
        "rel": "form_of",
        "target": "photo",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "photograph",
        "weight": 0.95
      }
    ]
  }
]

PROPOSED:
[
  {
    "lemma": "hotel",
    "pos": "N",
    "gloss": "a building where people can pay to stay and have services",
    "dewey": "647.94",
    "t1_decomposition": "something(x) and building(x) and provide(x, something)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "building",
        "weight": 0.92
      },
      {
        "rel": "hyponym",
        "target": "motel",
        "weight": 0.85
      },
      {
        "rel": "has_part",
        "target": "room",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "judge",
    "pos": "N",
    "gloss": "a person who decides if someone is guilty or not guilty in a court of law",
    "dewey": "347.014",
    "t1_decomposition": "someone(x) and decide(x, something)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "official",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "law",
        "weight": 0.95
      },
      {
        "rel": "agent_of",
        "target": "decide",
        "weight": 0.88
      }
    ]
  },
  {
    "lemma": "letter",
    "pos": "N",
    "gloss": "a written or printed message that is sent to someone",
    "dewey": "383.14",
    "t1_decomposition": "something(x) and written(x) and sent(x, someone)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "message",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "epistle",
        "weight": 0.78
      },
      {
        "rel": "domain_topic",
        "target": "postal_system",
        "weight": 0.82
      }
    ]
  },
  {
    "lemma": "material",
    "pos": "N",
    "gloss": "a substance that can be used to make things",
    "dewey": "620.11",
    "t1_decomposition": "something(x) and substance(x) and make(x, something)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "substance",
        "weight": 0.94
      },
      {
        "rel": "hyponym",
        "target": "fabric",
        "weight": 0.82
      },
      {
        "rel": "hyponym",
        "target": "metal",
        "weight": 0.84
      }
    ]
  },
  {
    "lemma": "planning",
    "pos": "N",
    "gloss": "the process of thinking about and deciding what to do",
    "dewey": "658.4012",
    "t1_decomposition": "something(x) and think(x, something) and decide(x, something)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "process",
        "weight": 0.9
      },
      {
        "rel": "derivation",
        "target": "plan",
        "weight": 0.95
      },
      {
        "rel": "domain_topic",
        "target": "management",
        "weight": 0.8
      }
    ]
  },
  {
    "lemma": "professor",
    "pos": "N",
    "gloss": "a person who teaches at a university",
    "dewey": "378.12",
    "t1_decomposition": "someone(x) and teach(x, something) and at(x, university)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "educator",
        "weight": 0.9
      },
      {
        "rel": "hypernym",
        "target": "academic",
        "weight": 0.9
      },
      {
        "rel": "domain_topic",
        "target": "academia",
        "weight": 0.85
      }
    ]
  },
  {
    "lemma": "showing",
    "pos": "N",
    "gloss": "an event where something is presented or displayed",
    "dewey": "791.43",
    "t1_decomposition": "something(x) and present(x, something) and see(x, something)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "presentation",
        "weight": 0.85
      },
      {
        "rel": "derivation",
        "target": "show",
        "weight": 0.9
      },
      {
        "rel": "synonym",
        "target": "screening",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "william",
    "pos": "N",
    "gloss": "a male given name",
    "dewey": "929.44",
    "t1_decomposition": "someone(x) and name(x) and male(x)",
    "depth": 4,
    "edges": [
      {
        "rel": "hypernym",
        "target": "name",
        "weight": 0.95
      },
      {
        "rel": "instance_of",
        "target": "given_name",
        "weight": 0.95
      }
    ]
  },
  {
    "lemma": "lake",
    "pos": "N",
    "gloss": "a body of water that is surrounded by land",
    "dewey": "551.482",
    "t1_decomposition": "something(x) and water(x) and surrounded(x, land)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "waterbody",
        "weight": 0.95
      },
      {
        "rel": "substance_of",
        "target": "water",
        "weight": 0.9
      },
      {
        "rel": "hyponym",
        "target": "pond",
        "weight": 0.75
      }
    ]
  },
  {
    "lemma": "photos",
    "pos": "N",
    "gloss": "images that are produced by a camera",
    "dewey": "770",
    "t1_decomposition": "something(x) and image(x) and produced(x, camera)",
    "depth": 4,
    "edges": [
      {
        "rel": "form_of",
        "target": "photo",
        "weight": 1.0
      },
      {
        "rel": "hypernym",
        "target": "photograph",
        "weight": 0.95
      }
    ]
  }
]
