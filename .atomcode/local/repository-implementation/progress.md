# SDD ledger - plan: openspec/changes/add-semantic-fact-repository/tasks.md

Base: d6ad206; branch implement-semantic-fact-repository-20261025.
Public contracts: remote main c01978c and local d6ad206 identical tree.
Gate PASS: 7 schemas / 64 shape / 30 semantic; runtime_verified=false.

|Task|Consistency|
|---|---|
|1|Tests and implementation refer to same interfaces; no contradiction found.|
|2|Tests and implementation refer to same interfaces; no contradiction found.|
|3|Tests and implementation refer to same interfaces; no contradiction found.|
|4|Tests and implementation refer to same interfaces; no contradiction found.|
|5|Tests and implementation refer to same interfaces; no contradiction found.|
|6|Tests and implementation refer to same interfaces; no contradiction found.|
|7|Tests and implementation refer to same interfaces; no contradiction found.|
|8|Tests and implementation refer to same interfaces; no contradiction found.|

|Shared pair|Producer / consumer|Finding|
|---|---|---|
|1/2|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|1/3|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|1/4|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|1/5|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|1/6|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|1/7|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|1/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|2/3|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|2/4|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|2/5|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|2/6|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|2/7|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|2/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|3/4|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|3/5|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|3/6|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|3/7|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|3/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|4/5|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|4/6|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|4/7|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|4/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|5/6|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|5/7|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|5/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|6/7|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|6/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|
|7/8|codec/types and staged store API, docs/fixtures carried forward|Sequential implementation, no competing ownership.|

Ruling: Historical planning-only text describes previous turn; current user requests implementation and Design Migration Plan step 2 explicitly allows subsequent apply.

Task 1: fix round 1/5 (2 addressed, 0 open codec findings; commits 6a03e0d..2b8d9e7). Scoped review approved.
Task 1: complete (commits d6ad206..2b8d9e7; 24 tests passed independently, 2026-10-25; review clean).
Implementation paused before task 2: Source ingress and source-less empty read/transfer results are unspecified in D3-D6; user approval pending for OpenSpec design/tasks amendment. No guessed API, SQLite not implemented.

Correction record (2026-10-25): The user approved correcting the proposal boundary before changing downstream artifacts. Proposal, design, and tasks were re-derived so the repository accepts submitted FactBatch values and returns the minimal matching fact set; independent Source mutation, source-less `batch=None` results, query orchestration, authorization, semantic judgment, no-hit explanation, and final-response handling are outside the repository. `openspec validate add-semantic-fact-repository --strict --no-interactive` passed after this re-derivation. Current plan frontier is 5/28 tracked tasks complete; implementation is not yet complete.

