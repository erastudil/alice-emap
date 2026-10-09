---
title: "emap — execution genome"
summary: "Alice 1.0 topological knowledge graph, lemma DAG verification, and invariant arbitration domain contract."
version: "1.1.0"
layer: genome
home: emap/AGENTS.md
dialect: progen syntax
status: canon
---

# emap

scope : Alice 1.0 topological knowledge graph and decision engine at C:\Users\jpm05\Documents\emap.

normative specification : SPEC.md.


## topological graph contract

graph manifold : 44000 lemmas and 24240 sense nodes organized under 24 closed relation names in emap.db and emap_csr.bin.

factual invariant : model weights carry zero truth value for factual claims; emitted facts derive solely from vetted cards or typed tool execution.

csr binary representation : export compressed sparse row binary format (emap_csr.bin) for zero-overhead graph traversal.


## verification and ponytail doctrine

verification gate : python build_emap_graph.py and python export_csr.py must execute cleanly with exit code 0.

ponytail wu wei : pull graph queries and lemma lookup into direct binary CSR operations without intermediate runtime overhead.

zero fake tests : all validation tests execute directly against sqlite database and binary CSR structures; synthetic mocks prohibited.

zero stubs : logic predicate stubs prohibited from production inference arbitration.
