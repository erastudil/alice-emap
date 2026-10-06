Repair the lexicon rows below.

The allow-list is the set of target lemmas you may name. It is the kernel list in your system instructions plus every lemma in this batch.

Return a JSON array with one object per input row, in the same order. Copy each lemma exactly.

ROWS:
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
