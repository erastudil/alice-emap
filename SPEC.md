---
title: "Alice 1.0 EMap Technical Architecture Specification"
version: "1.0.0"
status: canon
layer: architecture
home: emap/SPEC.md
dialect: progen-spec
---

# 1. System Boundary and Operating Invariants

system boundary: emap constitutes the immutable typed evidence-bearing knowledge graph; Alice 1.0 constitutes the constrained navigation and arbitration decision layer.
substrate isolation: model priors carry zero truth value for factual claims; semantic proximity directs search and never establishes truth.
ground truth precedence: deterministic tool execution strictly precedes valid factual zcab; valid factual zcab strictly precedes multi-source whitelisted web evidence; multi-source web evidence strictly precedes abstention.
provenance invariant: every factual emission carries an immutable provenance trace comprising an exact tool execution digest, a zcab content hash, or a whitelisted source URL span.
routing optimality: router path selection executes cost-sensitive classification against an empirical oracle under split-conformal risk bounds.
untrusted input boundary: all external web spans are consumed strictly as inert structured data tokens; executable instruction channels inside retrieved web data are structurally discarded.

# 2. Mathematical Representation and Graph Topology

## 2.1 Inventory and Identity Addressing

lemma count: 44000 normalized lexical lemmas grounded in the Goddard-Wierzbicka Natural Semantic Metalanguage kernel and English Wiktionary frequency ceiling.
sense count: 75000 discrete sense nodes yielding mean polysemy ratio 1.705.
node identity scheme: 32-bit stable unsigned integer address space.
address bit fields: bits 31..29 part of speech (3 bits, 8 classes); bits 28..26 abstraction tier (3 bits, T0 to T4); bits 25..0 local node identifier (26 bits, 67.1M capacity).
node type partitions: Lemma, Sense, Concept, Predicate, Taxon, Stack, Claim, Source, Tool, Procedure.
information content metric: IC(v) = -log P(v), where P(v) represents corpus-smoothed probability monotonically propagated over hypernym DAG satisfying P(v) >= sum(P(children)).

## 2.2 Product Manifold Geometry

geometric space: Riemannian product manifold M = L^32 x S^64 x R^128.
hyperbolic component: L^32 denotes 32-dimensional Lorentz hyperboloid manifold encoding hierarchical hypernymy and taxonomic depth.
lorentz inner product: <x, y>_L = -x_0 y_0 + sum_{i=1}^{31} x_i y_i.
lorentz distance: d_L(x, y) = arcosh(-<x, y>_L).
generality norm: origin distance ||x||_L encodes concept generality; small norm represents high abstraction.
spherical component: S^64 denotes 64-dimensional unit sphere encoding distributional, functional, and synonymic similarity.
spherical distance: d_S(x, y) = arccos(x . y).
euclidean relational component: R^128 denotes 128-dimensional vector space modeling typed relation operators via RotatE complex pairs with distance score_r(u, v) = -||u o rho_r - v||.
composite semantic distance: d_M(u, v) = sqrt(alpha * d_L(u, v)^2 + beta * d_S(u, v)^2 + gamma * ||u_e - v_e||^2).
discrete facets: sparse typed categorical fields comprising ontological_kind, domain_memberships, temporal_character, agency, materiality, quantity_dimension, causal_role.

## 2.3 Graph Data Structures and Storage

graph representation: directed typed multigraph G = (V, E, R, w, kappa) with 75000 senses, ~2.3M directed edges, 24 closed relation classes.
in-memory storage: Compressed Sparse Row (CSR) for outgoing traversals and Compressed Sparse Column (CSC) for incoming traversals, partitioned per relation type.
csr layout: indptr int32[N+1], indices int32[|E_r|], weights fp16[|E_r|], relation_type uint8[|E_r|].
graph memory footprint: core CSR/CSC topology occupies 18.2 MB; hypernym reachability bit-ancestor matrix occupies 4.5 MB; total graph structure remains L3/RAM resident under 25 MB.
vector embedding storage: manifold coordinates (75k x 224 x fp16 = 33.6 MB) plus text anchor embeddings (75k x 768 x fp16 = 115.2 MB) total 148.8 MB.
snapshot immutability: read-only memory-mapped binary images tagged with Merkle root digest over nodes, edges, zcabs, and schemas.

## 2.4 Cross-Domain Bridge Edges

bridge definition: typed non-hierarchical edge connecting taxonomically distant concepts exhibiting functional, structural, or mechanistic isomorphism.
structural bridge candidate score: b(u, v) = s_S(u, v) * s_struct(u, v) * (1 - exp(-d_L(u, v) / tau)) * I[depth(LCS(u, v)) <= D_0].
relational role signature: s_struct(u, v) represents Jaccard similarity across 1-hop typed role neighborhoods sig(u) = {(r, domain(n)) : (u, r, n) in E}.
taxonomic divergence constraint: D_0 = 3 forces lowest common subsumer to root levels, ensuring cross-domain validity.
bridge typology: identity, application, mechanism, measurement, analogy, constraint.
bridge traversal cost: elevated traversal penalty kappa prevents fact inheritance leaks; bridge edges permit candidate discovery and analogical retrieval exclusively.

# 3. Layered Abstraction Tiers (T0 to T4)

tier T0 lexical base: 44000 lemmas and 75000 senses; sense definitions strictly conform to inductive vocabulary bootstrap order.
tier T1 primitive predicates: 1500 nodes comprising 65 NSM primes (DO, HAPPEN, MOVE, HAVE, KNOW, WANT, PART, KIND, BEFORE), 1200 FrameNet-class schemas, and 250 typed attribute predicates.
semantic decomposition: T0 senses map to typed lambda-calculus ASTs of <= 32 nodes paired with sparse 1500-dimensional indicator vectors.
slot typing check: hyperbolic entailment cones on L^32 enforce argument types via closed-form angle evaluation in O(d_h).
tier T2 domain taxonomies: Dewey Decimal Classification spine (10 classes, 100 divisions, 1000 sections) integrated with specialized technical ontologies (QUDT units, IUPAC chemistry, NCBI taxonomy, ISO administrative regions).
dewey coordinate address: DDC.section (+) T1.predicate (+) T0.anchor denotes unique storage shelf.
tier T3 ontological meta-stacks: 120 meta-nodes structured across 4 orthogonal axes (BFO/DOLCE category, modal status, temporal volatility half-life tau_p, resolution affinity vector rho in Delta^4).
tier T4 answer stacks: governed materialized views of factual zcabs, Dewey-indexed passages, and pre-indexed retrieval tables.
inter-tier projection: soft projection matrix P_k in R^{|V_k| x |V_{k+1}|} induces upper adjacency A_{k+1}^{(r)} = P_k^T A_k^{(r)} P_k, ensuring higher tiers strictly aggregate verified empirical base evidence.

# 4. Storage Substrates and Tool Execution Contracts

## 4.1 Factual zcab Schema

```json
{
  "zcab_id": "u64_content_hash",
  "subject_id": "sense_id_or_entity_qid",
  "predicate_id": "t1_predicate_id",
  "object": {
    "type": "literal_or_id",
    "value": "scalar_value",
    "dimension_vector": [0, 0, 0, 0, 0, 0, 0],
    "unit": "qudt_symbol",
    "precision": 1e-6
  },
  "temporal_validity": ["t_start", "t_end"],
  "provenance": [{
    "source_id": "sha256_hash",
    "locator": "section_or_span",
    "retrieved_at": "iso_timestamp",
    "extraction_method": "deterministic_or_audited"
  }],
  "confidence_base": 0.995,
  "volatility_half_life": "tau_seconds",
  "verification_tier": "human_or_multisource",
  "supersedes": []
}
```

dimension vector: integer array delta in Z^7 representing SI base dimensions (Length, Mass, Time, Electric Current, Thermodynamic Temperature, Amount of Substance, Luminous Intensity).
freshness decay function: conf_eff(z, t) = conf_base(z) * exp(-(t - t_verified) / tau_p).
stack servability threshold: conf_eff(z, t) >= 0.97 qualifies zcab for immediate atomic emission; sub-threshold records trigger search hand refresh.
contradiction prevention: functional predicates reject overlapping temporal spans with conflicting objects at build time.

## 4.2 Search Hands (Whitelisted Agent Tools)

whitelist enforcement: out-of-band network proxies enforce strict protocol, host, port, path, and re-resolved IP restrictions; raw HTML is parsed into isolated frame slots.
extraction consensus: multi-source agreement requires score s(a*) >= theta_hand across >= 2 independent whitelisted domains or 1 authoritative domain with domain trust prior t_d in (0, 1].
write-back feedback: verified hand extractions enter candidate zcab intake queues with automatic promotion on k independent confirmations.

## 4.3 Deterministic Tool Engines

math engine: arbitrary precision rational CAS (SymPy / exact algebra kernel), interval arithmetic for transcendentals; returns exact rational and strict numerical bound.
units engine: dimensional algebra verifying delta_1 == delta_2 for addition/subtraction and summing delta vectors for multiplication; conversion executed via pinned rational transformation tables.
datetime engine: proleptic Gregorian calendar, pinned IANA tzdb version, leap second tables; outputs strict ISO 8601 strings and exact elapsed durations.
database engine: read-only parameterized query templates against pinned database snapshot identifiers.
exact solver: SAT/SMT (Z3 kernel), Mixed Integer Linear Programming (CBC/HiGHS) under strict execution time limits returning formal certificates of SAT, UNSAT, or TIMEOUT.

# 5. Alice 1.0 Decision Model Architecture

## 5.1 Formulation and Optimization Objective

action space: A = {RETRIEVE, HAND, COMPUTE, COMPOSE, ABSTAIN}.
decision objective: a* = argmin_{a in A} [(1 - p_a(q)) * C_err(q) + lambda_L * E[L_a] + lambda_$ * c_a] subject to calibrated p_a(q) >= 1 - epsilon_risk(q).
risk calibration: split-conformal calibration computes action thresholds per T2 domain risk class (health/financial epsilon=0.001, technical epsilon=0.01, general epsilon=0.05).

## 5.2 Model Components

query encoder: 350M parameter bidirectional int8 transformer producing span mention embeddings, T1 frame/slot hypotheses, T3 facet classifications, and query decomposition markers.
subgraph extractor: extracts bounded k-hop neighborhood (k <= 2, |V_sub| <= 512) around candidate senses; executes 2-layer Relational Graph Attention Network (R-GAT) over manifold coordinates.
coverage probe: non-neural sub-2ms exact index probe testing (sense, predicate, qualifiers) and checking inheritable hypernym ancestor chains.
router head: MLP over [E_cls (+) g_q (+) c_q (+) rho(T3) (+) volatility] outputting calibrated action probabilities.
dsl planner: 1.5B parameter int8 transformer invoked strictly for COMPUTE, HAND, or COMPOSE actions; constrained by Context-Free Grammar masking to emit valid typed execution plans.
executor: parallel asynchronous DAG scheduler executing tool calls, database lookups, and whitelisted web hands.
arbiter: enforces strict precedence lattice (COMPUTE > RETRIEVE > HAND > ABSTAIN) and verifies unit dimensionality, datetime bounds, and factual provenance.
renderer: template-based slot filler for atomic retrievals; constrained grounded language model for synthesized compositions with mandatory citation slot validation.

# 6. Resource Budgets and Latency Envelopes

token budget input: query text <= 512 tokens; planner context <= 1536 tokens; evidence context <= 2560 tokens; plan output <= 128 tokens; final render <= 384 tokens; hard ceiling 4096 tokens per call.
memory budget GPU: encoder int8 0.35 GB; planner int8 1.50 GB; hot graph topology 0.20 GB; total GPU VRAM allocation under 3.5 GB.
memory budget host: hot zcab cache and exact index 4.0 GB; HNSW passage vector index 6.0 GB; total host RAM allocation under 16.0 GB.
latency atomic retrieve: p50 <= 45 ms; p95 <= 120 ms (encoder 12 ms, probe 4 ms, R-GAT 6 ms, template render 10 ms, IPC 40 ms).
latency compute path: p50 <= 150 ms; p95 <= 350 ms (plan generation 180 ms, tool execution <= 50 ms).
latency hand path: p50 <= 900 ms; p95 <= 2500 ms (parallel network fetches 1200 ms, batched extraction 150 ms).
speculative execution: queries with router entropy H(p) > eta initiate top-2 actions concurrently, cancelling redundant branch upon arbitration.

# 7. Training and Construction Phases

phase P0 lexical inventory: normalize 44000 lemmas into 75000 senses; assign stable 32-bit IDs; calculate smoothed IC values; exit gate sense granularity kappa >= 0.75 on 2000 audited lemmas.
phase P1 graph structure: import lexical/taxonomic relations; enforce inverse symmetry; eliminate hypernym cycles; compile CSR/CSC binaries; exit gate 0 taxonomic cycles, edge precision >= 0.95.
phase P2 product manifold: train L^32 x S^64 x R^128 embeddings via Riemannian Adam; optimize L_hyp + L_sim + L_rel + L_norm; exit gate mAP >= 0.95, MRR >= 0.45, Spearman rho >= 0.65.
phase P3 bridge discovery: mine cross-domain analogies via S^64 proximity and structural role signatures; apply LCS root filter; exit gate 150000 bridges with audit precision >= 0.90.
phase P4 abstraction tiers: build T1 lambda-AST decompositions; map T2 Dewey taxonomies; populate T3 meta-stack facets; exit gate T1 verb/adj coverage >= 0.95, T2 assignment F1 >= 0.90.
phase P5 factual stores: ingest and dedup 20M-60M factual zcabs; attach 7-dim SI unit vectors; index Dewey shelves; exit gate zero functional contradictions, zcab precision >= 0.995.
phase P6 deterministic tools: implement typed DSL adapters for CAS math, dimensional units, Gregorian datetime, SQL templates, SMT solvers; exit gate 100% property-based test suite pass.
phase P7 whitelisted hands: configure domain proxy boundaries, extraction schemas, and consensus write-back queues; exit gate extraction precision >= 0.97 at theta_hand.
phase P8 decision model: generate 5M oracle training trajectories; train 350M encoder, R-GAT, and 1.5B grammar-constrained planner; exit gate routing accuracy >= 0.96.
phase P9 conformal calibration: calibrate action confidence thresholds on stratified held-out evaluations; exit gate empirical error <= epsilon_risk across all risk tiers.
phase P10 adversarial red-team: evaluate prompt injection resistance, false premise rejection, and stale fact eviction; exit gate 0 unprovenanced factual emissions, injection success < 0.1%.
