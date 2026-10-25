# �ֿ�߽���ͬԴ��

�����ֻ���� assets �е����¹�����Լ��û��˽����ʵ schema����Э�����䡢��Դ��ȡ��������ȷ���ж������� FactBatch ������� pipeline.schema.json#/$defs/fact_batch��contract-format.schema.json �� Query��output-schema.schema.json ������ Response�����߶����Ǵ洢���롣

## ������Դ����

Python ��λ�� scripts/semantic_facts����װ scripts/requirements.txt �� scripts ���� PYTHONPATH��ContractCodec(Path(.../assets)) �ṩ validate_batch/decode/encode������ʹ����Ե��롣JsonObject ��δУ�����룬���б߽�ֵ�����뾭��ͬԴ Draft 2020-12 schema���ܾ��� JSON������������δ�����ֶΣ�ContractError.location Ϊ JSON Pointer��������Ϊ /��

���� decode ���ص�Ԫ�� tuple[StoredRecord, ...]����Ԫ����Դ���������ͻ��м��ϣ��������� JSON blob��encode ������һ�������ף�����ʵ�����Ա��� sources����Ϊ���� sources.minItems=1��encode(()) �޷�����Դ�򣬶�λ /sources �ܾ������÷���ѡ��/�ϲ�ʱ��������װһ����������Դ���ײ����� decode�����ܰѶ����������ֱ��ƴ�ɹ���������Լ�������빫���ֶΡ�����Ŀ��ѯ���豣����֪Դ���ף�����α��Դ��¼��

ÿ�� ValueRow.payload �ǲ��ɱ� JSON �ַ�����value ���Է����¶���StoredRecord ���о�Ϊ frozen dataclass������Ϊ tuple���޸����������� value ��Ӱ���Ѳ���С�FactRow.payload ֻ��������ʵͷ��fields �Ƕ��� AttributeRow��SourceRow ����ÿ��������Դ״̬��InventoryRow ���湫��ֱ���嵥��identity-only children ��ԭ completeness�����ܰ��ӽڵ����ݱ��������ʵ��EntityRow ֻ������ʵ�� node��ֱ���嵥 target.node/children����ϵ�˵㡢֤�ݻ�ǰ���е����ñ���������ʵ�塣

## ���ݺ�˳��

identity_key(*parts) Ϊ���� UTF-8 JSON �ַ������飻û�зָ�����ײ��·���Ƶ������Է�֧����������������˽�� JSON ��Ԫ���룬�����˳�����ڹ������壻����ԭ˳���� ordinal �� JSON ������

| �ڲ��� | ��ȷ����������� |
| --- | --- |
| ��Ŀ�� project_key | [source_id, subject_id]������ subject_ref �����޶����ݣ����䱾�ֿ� FactFilter.project_keys�������� project_id |
| ʵ�� entity_key | [source_id, subject_id, node_id]��subject-only ���ÿɱ���Ϊ [source_id, subject_id]���������д���ʵ�� |
| ��ʵ fact_key | [source_id, subject_id, node_id, fact_id]����ͬ��ʵ ID�������Ĳ��ᰴ (����,����) �ϲ� |
| �ֶ� AttributeRow.key | [fact_key, /fields/ת���ֶ���]��RecordKey('attribute', fact_key, field_path) ��ά��Ŀ�� |
| ���� RelationRow.key | [�淶 JSON source ����, edge_id]���˵������������� edge_id ������target ���������� |
| ��Ƕ��ʽ�� key | [owner_key, �ֲ� assertion ·��, assertion �ڵı� JSON Pointer]���ֶε� owner Ϊ fact_key���ֲ�·��Ϊ field_path������/�嵥�� owner Ϊ��Ӧ�� key���ֲ�·��Ϊ /assertion�������� edge_id������ӵ�����ھֲ������������������ |
| ֤�� EvidenceRow.key | [source_id, evidence_id]��������ͬ����һ�У�relation ������ÿ�γ��ֵ� EvidenceLink �ϣ�ͬ����֤ͬ�����ݶ�λ�ܾ� |
| ��ͻ ConflictRow.key | [���ֵ������е� context.source_ids..., conflict_id]����ͬ��Դ�򲻺ϲ� |
| �嵥 InventoryRow.key | ['direct', ���� ordinal, �淶 JSON target, granularity, boundary]������û���嵥 ID���˼�ֻ���ڲ��ؽ�������¶�ɹ������� |
| ǰ�����ͻ���� | ӵ������ԭ���� Pointer ������ֲ�����ǰ��Ŀ�����������޶� fact_key + /fields/field�����������ϵ�� |

ͬһ FactBatch ���ظ����������޶���ʵ����һ�ɶ�λ�ڶ��� /facts/i �ܾ���������ȫ��ͬ���ֶβ��ཻ�����ݳ�ͻ���ظ�����ȥ�ء����ϲ�������д�����ύ��ͬ���� create �ݵ������ں��� store ���塣

���й������鱣�� ordinal���ֶζ��������������塣ʵ�尴���޶���ȥ�أ�identity-only child ��Ҫ����������ֶ���ʵ��source ״̬��֤��״̬����������� locator ���Զ�ȡ���ƶ���Ч��ʵ�� token/deleted�����������ԡ����񡢲�ѯ�ͻָ��ɺ��� store/transfer ����ʵ�֣�����δ�����Ѿ߱��־û���

## ʵ�� schema �� ��/�ֶ� �� �ؽ���

�±� `P` = pipeline.schema.json#/$defs/fact_batch��`C` = common.schema.json#/$defs���Ǻű�ʾ����ͬԴ����������ԣ��������� environment �����б�Ԫ�غͿ�������ʵ�ֻ�Ϊÿ��ʵ��Ҷ�Ӽ����������� FieldBinding(pointer, collection, row_key, column)��encode ���º˶������󶨼��ϣ�ȱʧ/�仯����λ�ܾ�������Ĭ��ֵ���롣JSON Pointer ���� ~0/~1 ת�塣

| ���� schema JSON Pointer | ����ʵ�� JSON Pointer | ���ͻ������ؽ� |
| --- | --- | --- |
| P/properties/contract_version��catalog_id | /contract_version��/catalog_id | StoredRecord ͬ���ֶΣ��ؽ�����ͷ |
| P/properties/sources��C/source/properties/* | /sources/i/* | SourceRow.payload��ordinal������ source_id/root/content_state/status/dirty/has_untracked/excludes ȫֵ |
| P/properties/facts��C/fact_node/properties/fact_id��node��fact_type��granularities | /facts/i/{fact_id,node,fact_type,granularities}/** | FactRow.payload��entity_key��fact_type��node ͬʱͶӰȥ�� EntityRow���ؽ���ʵͷ |
| C/fact_node/properties/fields �� allOf �� F1�CF18 �ֶ�Լ�� | /facts/i/fields/name/** | AttributeRow.payload��fact_key��field_path����������ʵ�ؽ����� fields����Ӳ�������Ի�ѡȡ�ֶ��Ӽ� |
| C/assertion/properties/origin��knowledge��reason��value��negative��context��coverage��basis��validity | ���� assertion ��ͬ���ֶ�/** | ���ԡ��������嵥�����б���ԭ�㼶������ֵ��ȫ���ݹ������֧���޶��񶨼� reason����������ʵ�� assertion |
| C/context/properties/* | .../context/{source_ids,conditions,environment,language_semantics}/** | ͬӵ���� payload��environment �������ֵ�����Ͱ� |
| C/coverage/properties/* | .../coverage/{domain,checked,excluded,completeness,method}/** | ͬӵ���� payload���޸������� |
| C/basis/properties/method��limitations | .../basis/{method,limitations}/** | ͬӵ���� payload��ԭ���ؽ� |
| C/basis/properties/evidence��C/evidence/properties/* | ���� evidence �б��� /i/*���� conflict �� cycle.execution_evidence�� | EvidenceRow.payload �� relation��EvidenceLink ���� owner_key��ԭ Pointer��ordinal��relation��encode �ù淶֤����+��� polarity ����ԭλ�� |
| C/basis/properties/premises��C/premise/properties/* | .../basis/premises/i/** | PremiseRow.payload��owner_key���������޶� target��encode ��ԭλ���ؽ������Ƶ��� |
| C/validity/properties/* | .../validity/{state,sources,reason}/** | ͬӵ���� payload��current/modified/deleted/premise_invalid/unknown ԭֵ�������ڲ� API �� valid ���������� state |
| P/properties/navigation��C/navigation_edge/properties/* | /navigation/i/{edge_id,source,target,relation,assertion}/** | RelationRow(navigation=True).payload��owner_key��source_key/target_key/relation���ⲿ�˵� target_key=None ����������ԭֵ���� |
| C/edge_set/properties/edges | /facts/i/fields/name/value/**/edges/j/**��/navigation/i/assertion/value/**/edges/j/**��/direct_nodes/i/assertion/value/**/edges/j/** | ����ͬԴ assertion λ��ͳһ�ݹ�ͶӰ RelationRow(navigation=False)��������ȷ owner��������ʽ�߼�����ԭ Pointer��ֻ����ʽ�߳�Ϊ��ϵ�У�references/��ѡ���ò����� |
| P/properties/direct_nodes��C/direct_inventory/properties/* | /direct_nodes/i/{target,granularity,boundary,children,assertion}/** | InventoryRow.payload��ordinal������ child ͶӰ EntityRow���������������ı� |
| P/properties/conflicts��C/conflict/properties/* | /conflicts/i/{conflict_id,members,reason,context,evidence}/** | ConflictRow.payload��ÿ�� members/i ���� ConflictLink(payload,target)��ԭ��Ա˳����������޶����ݱ��� |
| C/semantic_value��reference��reference_list��candidate_set��participant_set��binding_set��edge_set��cycle_value | ���� assertion/value/** | ȫ���ݹ����ݴ�������Ԫ�������ύ��ʽ edge_set ������ϵͶӰ�����Ѻ�ѡ����ȷ���ԡ����Ա���� external תΪ������ʵ |
| P �Ŀ� facts/navigation/direct_nodes/conflicts�����п�����/���� | ��Ӧ������ Pointer | envelope �������е���ȷ��ֵ�󶨣�������δ��/ȱ�ֶλ�ͬ |

����Ԫ����ԭʼ����ֵ���ھ�ȷ�ֶ�ά�����淶������ʽ��ϵ��֤�ݡ�ǰ�ἰ��ͻ�������ؽ�ʱ��Ӧ��λ�õ�Ȩ�����ǡ�����ֻ������ԭ���� Pointer����������ȱʧ�����塣�󶨽����ڲ�Ԫ���ݣ������빫�� FactBatch��û�й�����չ�ֶΰ����������� additionalProperties=false ������ܾ�δ֪�ֶΣ����ŵ� context.environment ���������

## ������֤�� fixture ��Դ

fixtures/full-batch.json ���� validation/stored-record.json �� batch ���Ʋ�����ͬԴ�Ϲ������֤�ݡ����� origin���޶��񶨡�ʧЧ�ֶΡ���Ҫǰ�ᡢ��������ͻ�벻���� child �嵥��response.json ֱ��ȡ���� validation/response.json ��Ϊ�ܾ���������ֻ֤���ֿ�߽���Ϊ����������ʵ��Ŀ�����Ѻ�ʵ��conftest �� scripts ���� sys.path ���ṩ���� validator ����ʱ���ݿ�·����

python -m pytest tests/repository/test_contract.py -q -p no:cacheprovider ��֤��ֵ round-trip���������顢�ܾ� Response/����/��Э�顢�����Ա��桢���ɱ��С�ȫҶ�󶨡�����ʵԴ���׼����޶����ݣ����������� SQLite ��Ϊ��


## �д����ξ����� source д�����

D3 Repository.apply ֻ���� ChangeSet��Mutation.target �� RecordKind û�� source��payload ��Ŀ���Ӧ��¼����ʵ/ʵ������û�� root/content_state/excludes ������ Source ���ݣ�apply Ҳû�� FactBatch ������codec �ܱ������ؽ����յ��� sources������ζ����Դ�����ܾ��ȶ� apply API �״ν���洢����˵�ǰ���ȱ�� source ����/������ڣ��޷���ƾ��������������ɹ��� FactBatch �ĳ־û���ǰ�ġ�����Դ���ס��� codec �ؽ�Լ���������µĲֿ����� API�����ܰ���Դ������ entity/fact payload��ȫ�ֻ�����������������ƹ������û�ȷ�Ϻ��޶����� design/tasks���ټ������� source д��� store ������

