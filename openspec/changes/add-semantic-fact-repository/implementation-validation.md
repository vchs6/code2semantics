# ʵʩ��֤��¼

## Group 1������׼����߽� codec��2026-10-25��

���ļ��ǵ�ǰ apply ��֤�ݣ���ʷ verification.md δ�Ķ���Ҳδ������ǰͨ��֤�ݡ���Ȩ�� design Migration Plan 2 �ĺ���ʵʩ����ִ�У�ԭ�滮�׶δ�ǲ���Ϊ��ǰ��ֹʵʩ�������ǰֻʵ���� 1�������� SQLite����ѯ�������˵�����ɡ�

### D1 �ⲿ׼��

�Ѽ���� assets �� 7 �� *.schema.json��fact-catalog.json��18 ��ʵ��4 ���ȡ�5 ��֯�ᣩ�� references/{fact-catalog,contract-format,output-schema,runtime-contracts}.md��FactBatch ��ȷλ�� pipeline.schema.json#/$defs/fact_batch��Query Ϊ contract-format.schema.json��Response Ϊ output-schema.schema.json�����߷��롣common.schema.json ��λ source��node_ref/subject_ref/external_ref��assertion(context/coverage/basis/origin/knowledge/validity)��premise��conflict��direct_inventory����Ҫǰ��Ϊ assertion.basis.premises��ʧЧ״̬Ϊ assertion.validity.state����ȷ���� Pointer��ȫ�ֶΰ󶨡���Դ������ӳ��� references/repository.md��

ʵ���������Ŀ¼Ϊ���ֿ����prepared deps ���ڱ��أ�����Ϊ��Ʒ���� vendoring����

    $env:PYTHONPATH='C:/Users/vchs6/.codex/tmp/code2semantics-python-deps'
    $env:PYTHONDONTWRITEBYTECODE='1'
    & 'C:/Users/vchs6/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 openspec/changes/epic-layered-semantic-fact-skill/validation/validate_contracts.py

�˳��� 0��ʵ�������

    {"schemas": 7, "shape_cases": 64, "semantic_cases": 30, "catalog_facts": 18, "status": "design_assets_pass", "runtime_verified": false}

��ֻ֤���������ʲ��������������У�飻runtime_verified=false ����ԭ�⡣�� revision/snapshot/refresh/response �洢��Ƿ�������У����������ܾ����Ը��ǡ�δ�޸Ĺ��� schema���������� references��Դ��Ŀ��� verification.md��

### RED �� GREEN

ʵ�ʲ��Ի�����Python ͬ�ϣ�PYTHONPATH=prepared deps + ���ֿ� skills/layered-semantic-facts/scripts��PYTHONDONTWRITEBYTECODE=1��

1. �ȴ��� tests/repository/conftest.py��fixtures/full-batch.json��fixtures/response.json��test_contract.py����ʱ semantic_facts ��Ʒ�������ڡ�
2. RED��python -m pytest tests/repository/test_contract.py -q���˳� 1����� .EEEEEEEEEEEEEEE [100%]��1 passed, 15 errors in 0.55s��Ψһ fixture ���� schema ��֤ͨ����15 ����� from semantic_facts.repository.contract import ContractCodec �� ModuleNotFoundError: No module named 'semantic_facts'�����ϼƻ�Ҫ���ȱʵ��ʧ�ܣ�������Ч fixture/����ʧ�ܡ�
3. ʵ�� immutable ������ codec ��ͬһ�����˳� 0��................ [100%]��16 passed in 1.45s��
4. ���������������ݻع���ԣ������� RED �˳� 1��2 failed, 16 passed in 1.74s��ʧ�ֱܷ�Ϊ�������ܶ����˳��Ӱ�졢���ñ�������Ϊʵ�塣
5. �޸���Դ�������������߽磻�м�ع鱩¶�󶨼��ϱȽ��ܶ������Ӱ�죺7 failed, 11 passed in 2.03s��ֻ�����ȷ�� Equal binding sets: True, lengths:379 379���׸�������� /contract_version �� /catalog_id�����󶨰� Pointer ���򣬲�����ȱʧ�󶨾ܾ���
6. ���� GREEN��python -m pytest tests/repository/test_contract.py -q -p no:cacheprovider���˳� 0��.................. [100%]��18 passed in 1.72s���رջ�������Ȿ�� .pytest_cache ACL ������δ�ı���Լ��ϡ�

### ��Χ�����

�� 1 �ṩ����Դ���׼�������ʵͷ/�ֶ�/��ʽ��ϵ/֤��/ǰ��/��ͻ����ȫҶ�󶨣��в��ṩ Repository��SQLite schema/���񡢱Ƚ� token����Χ��ȡ�������� transfer�����úϷ����뵱ǰ��Чǰ��հ������ store ����codec ���������ö�α��ʵ�塣���� evidence.relation ������ÿ�γ��ֵ������ϣ�ͬ ID ��ͬ polarity ���ϲ���ʧ������ʵ���Ա����Ϸ� sources��encode(()) ��ȷ�ܾ������ܷ�������Դ��

���ղ��䣺ȫ�� python -m pytest -q -p no:cacheprovider���˳� 0��18 passed in 2.04s��fixture ������������ shape_errors �� semantic_errors��stored_record ��װ������У���� fixture ��飩�����߾� []��git diff --cached --check �˳� 0���ݴ� 11 �������ļ����޹��� schema ��д������ 1.1�C1.5 �����޸Ķ�Ӧ׼ȷ checkbox �����»�ȡ apply ָ��ȷ�ϣ����� 5/38 complete����������δ��ǡ�


## Group 1 review round 1��2026-10-25��

����������� Important �����»ع���Ը��֣�ͬһ FactBatch ���ظ���ʵ���ݻ����ֶ��۵���д������/ֱ���嵥 assertion ����ʽ edge_set δͶӰ�������Ϊ python -X utf8 -m pytest tests/repository/test_contract.py -q -p no:cacheprovider������ͬ�ϡ�RED �˳� 1��..................FFF.FF [100%]��5 failed, 19 passed in 2.96s�������ظ�����������identical/different_value/disjoint_fields��δ�� ContractError���������嵥��©һ����ʽ�ߡ����лع�������ͨ������ schema���ֶ�λ��������֧�ֹ�����ͨ����

��С�޸��� GREEN �˳� 0��........................ [100%]��24 passed in 2.82s��validate_batch �ְ��������޶� fact_key �ܾ��κ������ظ���ʵ���ݣ���λ�ڶ��� /facts/i��������ͬ���ݣ���ȥ�ػ�ϲ�����ʽ����ȡͳһ���� fact-field��navigation.assertion �� direct_inventory.assertion �ĵݹ� semantic_value����ȷ owner ��ԭ Pointer �����Զ��ԣ�round-trip ����ֵ����ԭ���롣���� schema �� design/tasks δ�޸ġ�

Source ingress ��飺D3 apply(ChangeSet) û�� Source/FactBatch ���룬RecordKind û�� source����ʵ/ʵ�� payload ȱ���������� Source ״̬���������� API ȱ�ڡ�codec Դ���ױ������������д����ڣ�����ͨ�����ز���/����/����ʵ�� payload ���Բ��롣��������ڵĺ����洢ʵʩ�������û�ȷ����������޶���

## �׶�״̬�����׼������

2026-10-25����һ�� codec ���������鷢�־� RED��GREEN �޸���2b8d9e7���������޸���Χ�ĸ���ͨ��������������ִ�� `python -X utf8 -m pytest tests/repository -q -p no:cacheprovider`���˳� 0��24 passed in 2.75s����ֻ֤����ǰ codec �߽磬��֤�� SQLite ��ֿ�����ʵ����ɡ�

�ڶ���ǰֹͣ��D3 �� Mutation ֻ������Ŀ����û�� Source ��ڣ��޷��� FactBatch �����������Դ�����״�д�����£�D5 Ҫ�����Ȩ���Ϸ��ؿս������δ�涨����Դ����ʱ������� FactBatch.sources �� minItems=1������������밴 AGENTS �� 8/10 ��ȡ���û�ȷ�ϲ��� OpenSpec �޶� design/tasks �������������ʵ���мд������ֶλ�α����Դ����ǰ������ 1.1�C1.5 ��ɣ��������񱣳�δ��ɣ�δ������δ�鵵��



## 2026-10-26 当前来源有效性、规范化存储与传输 API

最新相关 CI: https://github.com/vchs6/code2semantics/actions/runs/40269799051

### 本轮实际验证

- `tests/repository`: 41 passed, 0 failed, 0 skipped.
- Capability matrix: 15 passed.
- Parser: 9 passed.
- Source scanner/direct inventory: 6 passed.
- Runtime source-to-query acceptance: 4 passed.
- Copied Skill packaging: 2 passed.
- Bounded tool executor: 3 passed.
- Combined information-needs/constructor/induction/query suite: 37 passed.
- Public contract validation and strict OpenSpec: passed.
- Product delivery gate: BLOCKED as expected because full S1–S12 product acceptance is not complete.

### New repository behavior

- SQLite now persists normalized `evidence`, `evidence_links`, `premises`, `inventories`, `conflicts`, and `conflict_links` in addition to sources/entities/facts/attributes/relations/submissions/source_heads. Relation rows retain the navigation classification.
- Current reads use source heads and filter assertions whose validity or evidence content state does not match the current source state. Filtering does not delete the underlying rows.
- `export_current()` exports current-head sources/facts plus current navigation/inventory/conflict records; stale historical fact rows remain in the local database but are not included in the current export.
- `import_current(batch, submission_key)` validates and appends through the same atomic write path. Invalid imports fail before mutation. Existing facts are never cleared to import a batch.
- Backup/restore continues to use SQLite backup and restores into a separate test database; invalid backups leave target state unchanged.

### Remaining repository gaps

The repository component is not fully complete. A public local-mutation API for field/relation/evidence/conflict invalidation, complete premise dependency propagation, graph-cycle/ancestor traversal, and full source-level import conflict policy remain pending. The RED-first sequence for the newest transfer tests was not captured as a separate CI run, so the associated task is not claimed complete solely from the GREEN regression.
