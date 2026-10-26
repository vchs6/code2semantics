# Tasks

## 1. Matrix contract and fixtures

- [x] 1.1 ���� `skills/layered-semantic-facts/assets/capability-matrix.json` �վ��� fixture���������� schema ��֤ `contract_version=1.0.0`��`entries=[]` ͨ�������� `pytest tests/capability_matrix/test_contract.py -q`��
- [x] 1.2 ��д schema �������ԣ�����ȱ�ٱ����ֶΡ��Ƿ� `tool_id`���ظ�����ֵ��δ֪�ֶΡ�`enabled=true` ȱ�� `acceptance`��`enabled=false` Я�� `acceptance`������ `pytest tests/capability_matrix/test_contract.py -q`��ȷ���� RED �� GREEN��
- [x] 1.3 ��д����Ϣ���󡢶����ԡ���ƽ̨�Ͷ����ѡ���� fixture����֤һ�� `tool_id` �ɸ��Ƕ�������Ҷ�����߿ɸ���ͬһ�������� `pytest tests/capability_matrix/test_contract.py -q`��

## 2. Deterministic matrix validation and maintenance

- [x] 2.1 �� `skills/layered-semantic-facts/scripts/semantic_facts/capability_matrix.py` ����������Ϳɶ�λУ����󣻱�д `validate(document)` ���Բ����� `pytest tests/capability_matrix/test_matrix.py::test_validation_errors -q`��
- [x] 2.2 ʵ�� `load()`����ȡ��У����󣬾ܾ��� JSON��schema ���Ϲ���ظ� `tool_id`������ `pytest tests/capability_matrix/test_matrix.py::test_load -q`��
- [x] 2.3 ʵ�� `replace(entries)` �� `upsert(entry)` ������ԤУ����ԭ��д�룻��֤ʧ��ʱԭ�ļ����䡢�ɹ�������¼��أ����� `pytest tests/capability_matrix/test_matrix.py::test_atomic_replace_and_upsert -q`��
- [x] 2.4 ʵ���ظ��ύ�ݵȺ�ʵ�ʱ����⣻��֤��ͬ��Ŀ���������ݱ仯���޸���Ŀ�Ų���һ�α�������� `pytest tests/capability_matrix/test_matrix.py::test_idempotent_updates -q`��
- [x] 2.5 ����ά���ӿ��ĵ���˵���о����ݡ�`acceptance`��`enabled` ������ʱ״̬�߽磻���� `pytest tests/capability_matrix/test_matrix.py -q`��

## 3. Candidate query

- [x] 3.1 ��д��ѯ RED ���ԣ�������Ϣ����ȫ��ƥ�䡢������ȫƥ�䡢ƽ̨��ȫƥ�䡢������ȫƥ���Լ������ѡȫ�����أ����� `pytest tests/capability_matrix/test_query.py -q`��
- [x] 3.2 ʵ�� `query(information_need_ids, language, platform, environment)`����ȷ��ƥ����򷵻��ȶ������ѡ�Ҳ�ִ�й��ߣ����� `pytest tests/capability_matrix/test_query.py -q`��
- [x] 3.3 ���ӿվ���δ֪��Ϣ�������ƥ�������ԣ�ȷ�����������պ�ѡ���������� `pytest tests/capability_matrix/test_query.py -q`��
- [x] 3.4 �����ѯ�߽��ĵ�����ȷ����ֻ�ṩ��ѡ��������ִ�С���Ȩ����ʵ��ȡ������ѡ�������ĵ�ʾ�����Ӧ�ĵ����ԡ�

## 4. Acceptance evidence and state isolation

- [x] 4.1 ���� `enabled`/`acceptance` ���������ԣ���ֻ֤�� `parser_development` ���зǿ�֤��ʱ�������ã����� `pytest tests/capability_matrix/test_acceptance.py -q`��
- [x] 4.2 ��������ʱ״̬������ԣ���֤�ɹ���ʧ�ܡ���ʱ�����Ե�����ʱ���ݲ���������Ҳ�����Զ��ı� `enabled`������ `pytest tests/capability_matrix/test_acceptance.py -q`��
- [x] 4.3 ���� `research_basis` �ǿտ�׷���ַ������ԣ�����֤ά���㲻����������ʱ֤�ݣ����� `pytest tests/capability_matrix/test_evidence.py -q`��

## 5. Integration and release gate

- [x] 5.1 ������ģ��������� `semantic_facts` ��������ڣ�����֤��������·�������� `pytest tests/capability_matrix -q`��
- [x] 5.2 ���о�����ԡ����� repository ���Ժ͹��� schema gate��ȷ�ϲ��ƻ� FactBatch��Query��Response ��Լ��������Ŀ�涨��ȫ���������
- [x] 5.3 ���� `openspec validate add-semantic-capability-matrix --strict --no-interactive`��ȷ�� proposal/spec/design/tasks ͨ��У�顣
- [x] 5.4 ��ɶ��� review������ review findings��������Ŀ��֤��¼�м�¼�������������ύ��ֻ��֤��������ѡ��������

## Workflow follow-up

- `/opsx-apply` ���� tasks.md ˳��ִ�У�ÿ��ʵ��������д RED����д��Сʵ�֣������� GREEN��
- ���ʵ�ֺͶ����������� `/opsx-archive`��

## 6. Expanded information-needs candidate matrix (2026-10-26)

- [x] 6.1 Add a small set of disabled research-candidate profiles mapped to the expanded F1–F18 need IDs: `python.compileall`, `python.pyproject-toml`, `rust.cargo-metadata`, `rust.cargo-check`, `rust.rust-analyzer`, `multi.ctags`, and `multi.ast-grep`. These are candidates for grouped coverage, not one tool per field.
- [x] 6.2 Keep every new candidate disabled and without `acceptance`; add a matrix test asserting that only the two initial Python/Rust syntax parser profiles are enabled and each research candidate remains disabled until parser-development acceptance.
- [x] 6.3 After CI probe evidence is recorded by `survey-info-acquisition-tools`, update candidate descriptions, versions, platform/environment constraints and native output formats. Do not enable any candidate in this task.
- [x] 6.4 Enable only candidates whose exact native-output parser and invocation profile passed parser-development acceptance; narrow each enabled entry to proven information needs and verify constructor selection and failure gaps.

Matrix candidate evidence: corrected CI probe run https://github.com/vchs6/code2semantics/actions/runs/40319334019. Python compileall and Cargo metadata temporary fixtures passed; Cargo/rustc versions were observed; rust-analyzer was not runnable; ctags/ast-grep/tree-sitter were absent. All six candidate entries remain disabled and have no acceptance evidence. Enabling remains pending parser-development acceptance.


### Narrow production profile enablement evidence (2026-10-26)

- `rust.cargo-metadata` is enabled only for `source.f4.kind` and `source.f6.kind`, with parser fixture, constructor persistence/reopen, CLI runtime acceptance and failure-mode evidence.
- `python.pyproject-toml` is enabled only for `source.f3.runtime` and `source.f6.kind`, with parser fixture, source-to-store/reopen and CLI runtime acceptance evidence.
- `tests/capability_matrix/test_contract.py` was updated to enforce these exact narrow acceptance records. CI https://github.com/vchs6/code2semantics/actions/runs/40353817807: capability matrix 15 passed, root/runtime acceptance 21 passed, induction/provider group 86 passed, strict OpenSpec passed. The product delivery gate remains blocked for full S1–S12.
- All remaining research candidates remain disabled. Per-profile acceptance does not certify unimplemented fields or the root production chain.
