# Proposal��������ʵ�ֿ⣩

## Why

��ѯ�͹���������Ҫһ���ɸ��á���׷�ݡ�������ά������ʵ�洢�������ǰȱ��һ��ֻΧ��������ʵ��������ͳһ�߽磬������ʵ���桢��ѯ���ź������ж����׻���һ��

## What Changes

- �������������ʵ��Լ�����������ʵ��ΪΨһ��ȡ���󣬰�ʵ�塢��ʵ���ֶΡ���ʽ��ϵ��֤�ݡ���Դ״̬�ͳ�ͻ�Ƚṹ���棻��Դ��Ϣ���ύ����ʵ�����档
- ֧����ʵ�����������������¡�ʧЧ��ɾ��������֤һ���ύ�е���ʵ�������״̬һ����Ч����ͬ�ύ�ɰ�ȫ�طš�
- �����÷��Ѿ�ȷ���Ĳ�ѯ�������ط�����������С������ʵ����������ʵ��֤�ݡ���Դ�����ġ���Ч�Ժͳ�ͻ�ȹ�����Լ��Ϣ��
- ���ύ���ݡ��ڲ����úʹ洢һ����ִ��ȷ����У�飻�ṹ���Ϲ���޷�����һ�µ��ύ����ܾ���
- **BREAKING**���ֿⲻ�ٳе���ѯ������š���Ȩ�жϡ�������ȷ���жϡ���ʵ������δ���н��͡�������Ӧװ�����Դ��Ŀɨ�裻��Щְ���ɵ��÷����ϲ��������
- **BREAKING**���ֿⲻ�ṩ��ʷ��ѯ���û��汾�����Э�飬������������Դ��Ŀ��Ҳ�������Э����ݺ�Ǩ����ڡ�

## Capabilities

### New Capabilities

- `semantic-fact-repository`����������ʵ��Լ��������������ʵ����������ȷ���Ĳ�ѯ����������С��ʵ����

### Modified Capabilities

�ޡ�

## Impact

- �ֿ�ʵ�֡�ͳһ Python ���ʽӿڡ���ʵ������롢����ά������ȷ��ѯ�͵��뵼���߽���Ҫ�����᰸����������
- ��ѯ����������������ԡ���Ȩ��Χ����ǰ��Դ��ʵ��δ���н��ͺ�������Ӧ��������������ʵ�������ֿⲻ�е���Щ������
- ������ʵ��Լ���������ӵ�У����᰸�����������ֶΡ����ı乫�� Schema��Ҳ�����Ƶڶ���Э�顣
- `design.md` �� `tasks.md` �Ǳ��᰸�޶����������������������ɲ���֤ǰ��������������������Ϊʵ�����ݡ�

## Clarification: semantic entity enrichment is the repository write model

The repository SHALL treat each submitted FactBatch as contributions to semantic entities and their facts, fields, relations and evidence—not as a replacement snapshot for an entity. The producer identity is not part of persistence identity and MUST NOT decide whether information is stored.

- If the semantic entity already exists but a valid fact/field/relation is new, persist the missing record while retaining existing records.
- If a field assertion already exists and the new submission adds a distinct valid evidence item/link supporting the same assertion, persist the new evidence/link without duplicating existing rows.
- If the same immutable identity is submitted with identical content, treat it idempotently and do not duplicate it.
- If the same immutable identity is submitted with incompatible content, reject it or represent the conflict according to the repository contract; never silently overwrite it.
- The constructor is responsible for request-driven information acquisition and a contract-valid FactBatch. It does not implement cross-request persistence deduplication or skip a whole entity because it already exists.

Acceptance must prove incremental enrichment of an existing entity, evidence addition, identical replay idempotency, immutable-identity conflict rejection, and preservation of unrelated facts. Apply this proposal before implementing these behaviors; the spec/design/tasks define the detailed tests.
