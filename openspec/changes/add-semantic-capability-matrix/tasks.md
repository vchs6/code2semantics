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

