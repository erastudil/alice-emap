Repair the lexicon rows below.

The allow-list is the set of target lemmas you may name. It is the kernel list in your system instructions plus every lemma in this batch.

Return a JSON array with one object per input row, in the same order. Copy each lemma exactly.

ROWS:
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
