# Tasks

������ʵ�ֿ� Implementation Plan

> ����ʵʩʹ�� TDD��ÿ����д��Ϊ���Բ����� RED����д��Сʵ�ֲ����� GREEN���ֿ�ֻ���� FactBatch ����ȷ���� Query����ʵ�ֲ�ѯ���š���Ȩ�������жϻ�������Ӧ��

## 1. ������Լ�߽�������

- [x] 1.1 ��������� FactBatch/Query/Response ��ʵ�� Schema ָ�룬����������Լ��֤����������˳�����ʲ�·��д�� `implementation-validation.md`��
- [x] 1.2 ��дͬԴ fixture �� codec ��Ϊ���ԣ��������ֶ���������Դ��֤�ݡ���Ч�ԡ���ͻ���޶��񶨡�partial child��������ֵ������/Response �ܾ���
- [x] 1.3 ���� `python -m pytest tests/repository/test_contract.py -q` �γ� RED��ȷ��ʧ������ȱ�� codec ���� fixture ��Ч��
- [x] 1.4 ʵ�� `ContractCodec`�����ɱ��ڲ������ͺ����� pointer �󶨣�����Ŀ�������ȫ�ֲ��� GREEN��
- [x] 1.5 ��ɶ�����鲢�ύ codec ����ĵ��������޸Ĺ��� Schema ������ڶ���Э�顣

## 2. SQLite ��ʵ��д���뾫ȷ��ȡ

- [x] 2.1 ��д `test_store.py`��ͨ��ͳһ `write(batch, submission_key)` д��ͬ�������ʵ��ͬ���Ͳ�ͬ�����ĺ͹�����Դ���رպ��ؿ���ȡ��ֱ�Ӻ��� facts/attributes/relations Ϊ�����ж��� FactBatch blob���� Query �������ֻ������С��ʵ����
- [x] 2.2 ���� `python -m pytest tests/repository/test_store.py -q` RED��ȷ��ʧ������ Repository/SQLite API ȱʧ��
- [x] 2.3 ʵ�����ӡ�DDL���������Դ�� FactBatch ���桢д��� `read(query)`����ƥ�䷵����ͨ�ռ��ϣ���ɨ����Դ������ȫ��ѯ������
- [x] 2.4 �������� 2 RED ���`test_contract.py` ����ʵ��ʱ SQLite �ؿ����� GREEN����¼·��ѡ�񡢲�ѯ���˺Ϳ�ƥ����Ϊ��
- [x] 2.5 �ύ store��ͳһ API�����Ժ��ĵ����˶�ֻ���������ļ���

## 3. ԭ�ӡ��ݵȺ;ֲ�ά��

- [x] 3.1 ��д������ԣ��Ƿ� FactBatch���Ƿ��ڲ����á��Ϸ� external��ͬ�������ظ��ύ��ͬ��ʶ��ͬ���ݡ���æ�Ϳ����ӳ¾�д���п��ж����ԣ���֤ʧ�ܺ��״̬���䡣
- [x] 3.2 ���� `python -m pytest tests/repository/test_transactions.py -q` RED��
- [x] 3.3 ʵ�ֵ�����д�롢�淶���ύժҪ���ݵ�ȷ�ϡ���ͻ�ܾ�������������ͼУ�飻����Ĭ���ǳ�ͻ��
- [x] 3.4 ��д�����оֲ��ֶΡ���ϵ��֤�ݡ���ͻ��ʧЧ��ɾ��ά�����ԣ�ȷ���޹���ʵ�� token ���䣬��Ӱ���¼��������һ�¡�
- [x] 3.5 �������񡢴洢�� codec ���� GREEN�����ύ����ʵ�֡����Ժ��ĵ���

## 4. ��ǰ״̬��ȡ���н��ϵ����

- [x] 4.1 ��д��Ч�Ժ�ǰ����ԣ�ʧЧ��ʵ��������Ч�������Ҫǰ�ᰴ���ύ״̬��飬֤�ݺ� coverage ԭ���������ֿⲻ������Դ�ļ���
- [x] 4.2 ���� `python -m pytest tests/repository/test_validity.py -q` RED��
- [x] 4.3 ʵ����ȷǰ��հ���ʧЧ״̬���ˡ�ά����ȡ�� token ��飻������δ����������Ӱ�죬�����Ϳս����
- [x] 4.4 ��дͼ���ԣ��ุ���رߡ���ϵȥ�ء����/��Ԥ�㡢external �˵����С��ʵ��ͶӰ��
- [x] 4.5 ������Ч�ԡ�ͼ������ʹ洢���� GREEN���ύʵ�֡����Ժ��ĵ���

## 5. ���������롢������ָ�

- [x] 5.1 ��д������ԣ���Ч/ʧЧ��ʵ����Դ��֤�ݡ���ͻ��ǰ�ᱣ�棻��⵼��������ڲ� token��ȱʧ���á���ͬ�������ݡ�Խ��������𻵱��ݾ�����ܾ���
- [x] 5.2 ���� `python -m pytest tests/repository/test_transfer.py -q` RED��
- [x] 5.3 ʵ�ֵ�ǰ��ʵ���������롢SQLite һ�±��ݻָ���ʧ�ܱ�������������ʷ���ݻ������ԴЭ�顣
- [x] 5.4 ���д��䡢codec����Ч�Բ��� GREEN�����鵼��������Ӷ���һ�²��ύ�����ļ���

## 6. �ֿ��������

- [x] 6.1 ��д��ģ���������ڲ��ԣ�FactBatch д�롢�ؿ���ȡ���ֲ�ά������Ч�ԡ����޹�ϵ��ȡ����������ͱ��ݻָ�����ѯ�����ɲ���ֱ���ṩ��
- [ ] 6.2 ���� `python -m pytest tests/repository/test_acceptance.py -q` RED������¶ǰ��ȱ�ݣ��ص���Ӧ���Ȳ��������޸���
- [x] 6.3 ���� `python -m pytest tests/repository -q` ���ڶ������ض���֤����¼ʵ������˳��롢����������������ӳ�䵽 `implementation-validation.md`��
- [ ] 6.4 �ύ���������ļ�����ȷ����ѯ/����������������������𣬲��Զ�������鵵��

## Workflow follow-up

- �������ɲ�ѯ�빹�������ɺ��ٽ��ж˵�����֤��
- ����ʵ�ֺ���֤��ɺ󣬰���Ŀ������鲢�鵵 OpenSpec �����



## Verified implementation evidence (2026-10-26)

- Atomic immutable row writes now persist sources, entities, facts, attributes, relations, evidence, evidence links, premises, direct-node inventories, conflicts and conflict links. Repeated identity/payload conflicts are rejected rather than replaced.
- Repository reads use source_heads, return current source facts only, and filter assertions with non-current validity or stale evidence content states. Invalid/stale rows remain in SQLite; no delete is used for invalidation.
- Added tests: tests/repository/test_validity.py and tests/repository/test_acceptance.py. Transfer tests restore to a separate database; acceptance tests verify normalized row counts, query, backup/restore equality and conflict rollback.
- CI run https://github.com/vchs6/code2semantics/actions/runs/40268373808 is validating the updated repository and package suites. The previous completed repository suite passed 39 tests before the newest normalized row and acceptance changes; strict OpenSpec passed. Use the linked run for final pass/fail.
- Still pending: a public local-mutation API for field/relation/evidence invalidation, complete premise dependency invalidation and graph-cycle traversal tests, current import/export API, and full repository acceptance after those APIs land. These tasks remain pending; this evidence does not claim the whole repository component complete.


## 2026-10-26 implementation evidence

- `Repository.export_current()` exports current source-head facts, navigation, inventories and conflicts while excluding stale assertions from the exported view; local historical rows remain stored.
- `Repository.import_current(batch, submission_key)` validates and appends through atomic write; invalid imports fail before mutation. Backup/restore tests use separate databases and preserve row counts.
- Normalized evidence/premise/inventory/conflict rows and navigation classification are persisted and read back.
- Validation record: `implementation-validation.md`. CI run https://github.com/vchs6/code2semantics/actions/runs/40269799051: repository 41 passed; strict OpenSpec and all component test groups passed. Product delivery gate intentionally remains blocked.
- Still pending: RED-first evidence for newest transfer tests; public local mutation/invalidation API; complete premise propagation, graph-cycle/ancestor traversal and broader import conflict policy. Do not infer these from export/import tests.


## Bounded graph traversal evidence (2026-10-26)

- Implemented `Repository.traverse_navigation(start, max_depth, max_edges)` in `skills/layered-semantic-facts/scripts/semantic_facts/repository/store.py`.
- Traversal starts only from a current source-head node, reads current in-scope navigation edges, uses visited-node and visited-edge sets to terminate cycles, preserves distinct parent edges, deduplicates equivalent edges via repository read semantics, returns external/cross-source references as terminal references without expanding them, and reports explicit depth/edge truncation.
- RED was observed in CI run https://github.com/vchs6/code2semantics/actions/runs/40297171108 because the API did not yet exist. The first implementation run exposed a disconnected multi-parent test fixture; the fixture was corrected to connect the second parent from the root rather than weakening the assertion.
- GREEN evidence: https://github.com/vchs6/code2semantics/actions/runs/40297475469 — repository suite 53 passed; matrix 15, parser 9, scanner 7, source acceptance 4, packaging 2, executor 3, producer dispatch 3, combined information-needs/constructor/induction/query 51 passed; strict OpenSpec passed. Product delivery gate remains blocked for full S1–S12 acceptance.
- This completes bounded repository graph traversal tests for cycles, multi-parent edges, equivalent-edge deduplication, external terminal references, and budget truncation. It does not complete query-level S1–S12 or the full product lifecycle.


## Transaction concurrency and graph acceptance evidence (2026-10-26)

- Added `test_concurrent_identical_submission_is_idempotent_across_connections` in `tests/repository/test_transactions.py`. RED: CI https://github.com/vchs6/code2semantics/actions/runs/40298073017 failed with `UNIQUE constraint failed: submissions.submission_key`, demonstrating the concurrent replay race.
- GREEN: `Repository.write` now re-reads the submission key after a transaction uniqueness race. If the winner committed the same digest, the loser returns the same receipt and reasserts the current source head; a different digest still raises `WriteConflict`.
- CI after fix: https://github.com/vchs6/code2semantics/actions/runs/40298151751 — repository 54 passed; matrix 15; parser 9; scanner 7; runtime acceptance 5; packaging 2; executor 3; producer dispatch 3; combined information-needs/constructor/induction/query 52 passed; strict OpenSpec passed. Product delivery gate remains blocked for full-system acceptance.
- Graph traversal: `Repository.traverse_navigation` and `test_bounded_navigation_traversal_handles_cycles_multi_parent_and_external_refs` cover bounded traversal, cycle termination, multi-parent edges, edge deduplication, external terminal references, and depth/edge budgets. Evidence: https://github.com/vchs6/code2semantics/actions/runs/40297691458.
- Remaining pending items are intentionally not checked: 5.2 still lacks a separately captured RED run for transfer tests; 6.2 still requires a demonstrated RED-first full repository acceptance path, and 6.4 remains pending until that acceptance is complete.


## Transfer validation RED/GREEN evidence (2026-10-26)

- RED: `test_restore_rejects_empty_sqlite_file_without_changing_fact_history` failed in CI https://github.com/vchs6/code2semantics/actions/runs/40298339861 because an empty but valid SQLite file passed the prior conditional schema check and could replace the target database.
- Fix: `Repository.restore` now requires the full repository table set unconditionally before copying a backup. Empty/foreign SQLite databases are rejected before target mutation.
- GREEN and focused CI: https://github.com/vchs6/code2semantics/actions/runs/40298437864 — repository 55 passed; focused transaction 6 passed; focused transfer 6 passed; repository acceptance 3 passed; matrix 15; parser 9; scanner 7; runtime acceptance 5; packaging 2; executor 3; producer dispatch 3; combined information-needs/constructor/induction/query 52 passed; strict OpenSpec passed.
- The product delivery gate remains intentionally BLOCKED for full S1–S12 acceptance. Repository task 6.2/6.4 remain pending until their complete RED-first acceptance obligations and broader import/local-mutation policy are fully demonstrated.
