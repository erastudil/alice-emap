Repair the lexicon rows below.

The allow-list is the set of target lemmas you may name. It is the kernel list in your system instructions plus every lemma in this batch.

Return a JSON array with one object per input row, in the same order. Copy each lemma exactly.

ROWS:
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
