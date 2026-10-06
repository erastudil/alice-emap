Repair the lexicon rows below.

The allow-list is the set of target lemmas you may name. It is the kernel list in your system instructions plus every lemma in this batch.

Return a JSON array with one object per input row, in the same order. Copy each lemma exactly.

ROWS:
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
