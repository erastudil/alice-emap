Repair the lexicon rows below.

The allow-list is the set of target lemmas you may name. It is the kernel list in your system instructions plus every lemma in this batch.

Return a JSON array with one object per input row, in the same order. Copy each lemma exactly.

ROWS:
[
  {
    "id": 2263,
    "lemma": "assembly",
    "pos": "N",
    "gloss": "gathering",
    "dewey": "302",
    "t1_decomposition": "GATHER(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "gathering",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2264,
    "lemma": "breakfast",
    "pos": "N",
    "gloss": "morning meal",
    "dewey": "641",
    "t1_decomposition": "MEAL(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "meal",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2270,
    "lemma": "combination",
    "pos": "N",
    "gloss": "mixture",
    "dewey": "001",
    "t1_decomposition": "MIXTURE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "mixture",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2272,
    "lemma": "customer",
    "pos": "N",
    "gloss": "buyer",
    "dewey": "658",
    "t1_decomposition": "BUYER(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "synonym",
        "target": "buyer",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 2274,
    "lemma": "desire",
    "pos": "N",
    "gloss": "wish",
    "dewey": "152",
    "t1_decomposition": "WISH(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "synonym",
        "target": "wish",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 2276,
    "lemma": "draft",
    "pos": "N",
    "gloss": "preliminary version",
    "dewey": "808",
    "t1_decomposition": "VERSION(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "version",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2284,
    "lemma": "humans",
    "pos": "N",
    "gloss": "people",
    "dewey": "599",
    "t1_decomposition": "PEOPLE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "synonym",
        "target": "people",
        "weight": 0.9
      }
    ]
  },
  {
    "id": 2285,
    "lemma": "hundreds",
    "pos": "N",
    "gloss": "large number",
    "dewey": "513",
    "t1_decomposition": "NUMBER(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "number",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2290,
    "lemma": "markets",
    "pos": "N",
    "gloss": "places for trade",
    "dewey": "381",
    "t1_decomposition": "PLACE(x)",
    "depth": 3,
    "edges": [
      {
        "rel": "hypernym",
        "target": "place",
        "weight": 0.95
      }
    ]
  },
  {
    "id": 2291,
    "lemma": "medium",
    "pos": "N",
    "gloss": "intermediate",
    "dewey": "001",
    "t1_decomposition": "INTERMEDIATE(x)",
    "depth": 2,
    "edges": [
      {
        "rel": "hypernym",
        "target": "intermediate",
        "weight": 0.95
      }
    ]
  }
]
