# Design

## Context

��������� `proposal.md` �� `specs/semantic-capability-matrix/spec.md`��Ϊ������������ȷ��ʵ�ַ�ʽ������ `skills/layered-semantic-facts/assets/capability-matrix.schema.json` �Ѷ�����󹫹��ֶΡ�`tool_id` ��ʽ������Լ���Լ� `enabled` �� `acceptance` ��������ϵ��

�������ݰ�����`survey-info-acquisition-tools/research/semantic-tooling-survey.md` �� 1 �ڵ���Ϣ���󡢵� 3 �ڵĹ���������ƽ̨��Χ���� 4 �ڵ���Ϣ����ӳ�䡢�� 5 �ڵĺ�ѡ�ж��͵� 6 �ڵı߽磻`survey-semantic-fact-requirements/research/semantic-fact-requirements.md` �� Q1�CQ12��R1�CR16�������� R8��R12��R13��R15��

## Goals / Non-Goals

**Goals:**

- �� `skills/layered-semantic-facts/assets/capability-matrix.json` ����һ��ͨ������ schema У��ľ��󣬳�ʼ `entries` Ϊ�ա�
- �� `skills/layered-semantic-facts/scripts/semantic_facts/capability_matrix.py` �ṩȷ���Եļ��ء�У�顢ά�����ݵȸ��ºͺ�ѡ��ѯ������
- ���湤������Ϣ����������͡����ԡ�ƽ̨�����������÷�ʽ����Ϲ�ϵ�����ƺ��о����ݵĹ�ϵ��
- Ҫ�� `enabled=true` ����Ŀ���� `actor=parser_development` �ҷǿյ�����֤�ݡ�
- ��ѯʱҪ����Ϣ����ȫ��ƥ�䣬���ԡ�ƽ̨�ͻ�����ȫƥ�䣬������ȫ�����������ĺ�ѡ��
- ��У��ʧ��ʱ����ԭ���󲻱䣻����ʱ״̬���������

**Non-Goals:**

- ��ִ�С���װ��̽�����ȹ��ߡ�
- ��ɨ����Ŀ����������Ϣ���󡢲���ȡ������ʵ��
- �����ݹ������гɹ���ʧ�ܡ���ʱ�������Զ��ı����״̬��
- ���� AI ������ʱ���䡢�ƶϻ��д������Ŀ��
- �����𹤾���ϱ��š�Ψһ����ѡ������ղ�ѯ��Ӧ��

## Decisions

### 1. ������ JSON schema ��ΪΨһ������Լ

ʵ��ʹ������ `capability-matrix.schema.json` У����󣬲�������Ŀ���� Python `jsonschema` У��������У���������ܶ�λ������·����

���ݣ����� schema��`semantic-tooling-survey.md` �� 3�C5 �ڣ�`semantic-fact-requirements.md` R8��R15��

��ѡ������ά���ڶ��� Python �ֶ�У�飬�ѷ������Ϊ������빫�� schema Ư�Ƶĵڶ�����Լ��

### 2. ʹ�õ�һ JSON �����ĵ�

�����ļ��̶�Ϊ `skills/layered-semantic-facts/assets/capability-matrix.json`����ʼ����Ϊ��

```json
{
  "contract_version": "1.0.0",
  "entries": []
}
```

������Ŀ�� `tool_id` ��Ϊ������Ψһ�ȶ����ݣ�ͬһ��Ŀ�ظ��ύ�����ݵȣ�ʵ�ʱ��ͨ��ά���ӿ���ɡ�

���ݣ�proposal �С���ʼΪ�ա���ά���ӿڵ�Լ�������� schema��`semantic-tooling-survey.md` �� 5�C6 �ڣ�`semantic-fact-requirements.md` R2��R4��R15��

��ѡ�����ǰ����߲�ֶ���ļ����ѷ������Ϊ��������ļ�Ψһ�ԡ�ԭ�Ӹ��º�һ�������⡣

### 3. ά���ӿ�������У����ԭ��д��

ģ��̶�Ϊ `skills/layered-semantic-facts/scripts/semantic_facts/capability_matrix.py`�����ṩ����ְ��

- `load()`����ȡ��У����������
- `validate(document)`��ִ�� schema��Ψһ���ݡ��о����ݺ���������У�飬���ؿɶ�λ����
- `replace(entries)`������У���ѡ�����ԭ���滻��
- `upsert(entry)`���� `tool_id` �ݵȸ��µ�����Ŀ��
- `query(information_need_ids, language, platform, environment)`������ƥ���ѡ��

`research_basis` ֻҪ��ǿա���׷�ݵ��ַ�����ά���㲻���ַ�������Ϊ����ʱִ��֤�ݣ�Ҳ���Զ���֤�ⲿ�о��ļ�������д�������ڴ����������У�飬ʧ��ʱԭ�ļ����ֲ��䡣

���ݣ�proposal ��ά���ӿ�Ҫ��`semantic-tooling-survey.md` �� 4�C6 �ڣ�`semantic-fact-requirements.md` R8��R12��R13��R15��

��ѡ�������������÷�ֱ���޸� JSON���ѷ������Ϊ���ƹ�ͳһУ���ԭ�Ӿܾ���

### 4. ��ѯҪ����Ϣ����ȫ��ƥ���һ�����ȫ���

��ѯ����� `information_need_ids` ����ȫ������ѡ��Ŀ���ǣ�`language`��`platform` �� `environment` ������ȫ���ƥ�䡣�����������ƥ���ѡ�������ȶ��� `tool_id` ˳�����С��վ������ƥ�䷵�ؿպ�ѡ���ϣ�δ֪��Ϣ�����������������ά��/��ѯ�ӿڶ�λ���ء�

��ѯ��ִ�й��ߣ�Ҳ������÷���Ψһѡ��

���ݣ��û�ȷ�ϵ�Լ����`semantic-tooling-survey.md` �� 4�C6 �ڣ�spec �С�ֻ���غ�ѡ���Ͷ๤�߸���ͬһ����ĳ�����`semantic-fact-requirements.md` R6��R14��R16��

��ѡ��������һ��Ϣ����ƥ�䡢��������ƥ����ڲ������ֻ����һ�����ߣ��ѷ������Ϊ�ᶪʧ���ǹ�ϵ�ҳ�������ְ��

### 5. enabled ������ʱ״̬�ϸ����

`enabled=true` ������� `acceptance.actor=parser_development` ������һ������֤�ݣ�`enabled=false` ����Я�� `acceptance`������ schema ��ά��ģ������ý�������ʱ�ɹ���ʧ�ܡ���ʱ�����Ի��Զ�״̬�ֶΡ�

���ݣ��û�ȷ�ϵ�Լ�������� schema��proposal �� spec �����ձ߽磻`semantic-tooling-survey.md` �� 5�C6 �ڣ�`semantic-fact-requirements.md` R15��

��ѡ�����Ǹ����о����ݻ�����ʱ�ɹ��Զ����ù��ߣ��ѷ������Ϊ�о�����˵����һ�����н����������� parser-development ����֤�ݡ�

## Risks / Trade-offs

- [Risk] �о������������ַ��������÷������ṩ�޷����˵����� �� Ҫ��ǿտ�׷���ַ�������Ϊȱʧ�������Ӿܾ����ԣ��ⲿ�ļ�������У�����ں����о�������Χ��
- [Risk] `enabled` �����Ϊ����ʱ�ɹ� �� �ĵ��Ͳ�����ȷ��������״̬������ʱ״̬������ܾ�����ʱ�ֶΡ�
- [Risk] �����󹤾߱������ɶ����Ŀ �� һ�� `tool_id` ������ `information_need_ids`�������Զ�����߸���ͬһ����
- [Risk] ����ʧ����ɲ���д�� �� ������У�飬��ͨ����ʱ�ļ��滻������ȷ��ʧ�ܺ�ԭ�ļ����ݲ��䡣
- [Risk] ��Ϣ�����嵥������ѯ����Ư�� �� ��ѯֻ�����ѵǼǵ������ʶ��δ֪��ʶ���ؿɶ�λ����

## Migration Plan

1. �����վ��� JSON �ļ���ͨ������ schema У�顣
2. �ȼ���У�顢���ء�ά���Ͳ�ѯ���ԣ���ʵ��ģ�顣
3. ͨ��ά���ӿ�¼���о�����֧�ֵĺ�ѡ���ߣ��� parser-development ����֤�ݵ���Ŀ���� `enabled=false`��
4. ���о�����ԡ����� repository ���Ժ� OpenSpec �ϸ�У�顣
5. �ع�ʱ�ָ���һ��ͨ�� schema У��ľ����ļ������޸��о����档

## Parser-observation coverage is the source of truth

A matrix entry's `information_need_ids` SHALL describe the observations the exact parser/invocation profile can currently produce and the constructor can consume, not every fact a tool might theoretically help research. Narrow a profile to proven need IDs; keep it disabled if the parser emits observations but no accepted FactBatch mapping exists. For example, the current `python.compileall` adapter emits only `source.f9.language-semantics`; it does not establish declaration, scope, error-handling or runtime semantics. Candidate capability claims remain disabled until parser and constructor mapping acceptance both pass.
