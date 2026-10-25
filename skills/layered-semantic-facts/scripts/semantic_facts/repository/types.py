"""�ֿ��ڲ����ͣ�������ڶ��׹��� wire Э�顣"""
from dataclasses import dataclass
import json
from typing import Literal

JsonObject = dict[str, object]
RecordKind = Literal["entity", "fact", "attribute", "relation", "evidence", "conflict"]


@dataclass(frozen=True)
class RecordKey:
    kind: RecordKind
    key: str
    field_path: str | None = None


@dataclass(frozen=True)
class Mutation:
    action: Literal["create", "update", "invalidate", "delete"]
    target: RecordKey
    payload: JsonObject | None
    expected_token: str | None


@dataclass(frozen=True)
class ChangeSet:
    submission_key: str
    mutations: tuple[Mutation, ...]


@dataclass(frozen=True)
class CommitReceipt:
    submission_key: str
    digest: str
    affected: tuple[RecordKey, ...]


@dataclass(frozen=True)
class FactFilter:
    project_keys: tuple[str, ...]
    subjects: tuple[str, ...] = ()
    fact_types: tuple[str, ...] = ()
    validity: Literal["valid", "all"] = "valid"


@dataclass(frozen=True)
class RecordReadResult:
    target: RecordKey
    value: object
    metadata: JsonObject
    token: str
    valid: bool
    deleted: bool


@dataclass(frozen=True)
class ReadResult:
    batch: JsonObject
    tokens: dict[RecordKey, str]


@dataclass(frozen=True)
class TraversalResult:
    records: ReadResult
    truncated: bool
    reason: Literal["depth", "edges"] | None


class ContractError(ValueError):
    def __init__(self, location: str, reason: str):
        self.location = location
        self.reason = reason
        super().__init__(f"{location}: {reason}")


class ReferenceError(ValueError):
    def __init__(self, target: RecordKey):
        self.target = target
        super().__init__(f"Invalid reference: {target}")


class WriteConflict(ValueError):
    def __init__(self, target: RecordKey, reason: str):
        self.target = target
        self.reason = reason
        super().__init__(f"{target}: {reason}")


class StorageError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def identity_key(*parts: str) -> str:
    """�������ݵ�����Ԫ����룻��������/·��/����״̬�Ƶ���"""
    return json.dumps(parts, ensure_ascii=False, separators=(",", ":"))


def project_key(node: JsonObject) -> str:
    return identity_key(node["source_id"], node["subject_id"])


def entity_key(node: JsonObject) -> str:
    parts = (node["source_id"], node["subject_id"])
    return identity_key(*parts, node["node_id"]) if "node_id" in node else identity_key(*parts)


def fact_key(fact: JsonObject) -> str:
    node = fact["node"]
    return identity_key(node["source_id"], node["subject_id"], node["node_id"], fact["fact_id"])


@dataclass(frozen=True)
class ValueRow:
    key: str
    pointer: str
    payload: str
    ordinal: int

    @property
    def value(self) -> JsonObject:
        # A fresh value prevents nested mutation of the frozen stored view.
        return json.loads(self.payload)


@dataclass(frozen=True)
class SourceRow(ValueRow):
    pass


@dataclass(frozen=True)
class EntityRow(ValueRow):
    project_key: str


@dataclass(frozen=True)
class FactRow(ValueRow):
    entity_key: str
    fact_type: str


@dataclass(frozen=True)
class AttributeRow(ValueRow):
    fact_key: str
    field_path: str


@dataclass(frozen=True)
class RelationRow(ValueRow):
    owner_key: str
    source_key: str | None
    target_key: str | None
    relation: str
    navigation: bool


@dataclass(frozen=True)
class InventoryRow(ValueRow):
    pass


@dataclass(frozen=True)
class EvidenceRow(ValueRow):
    pass


@dataclass(frozen=True)
class EvidenceLink:
    owner_key: str
    evidence_key: str
    pointer: str
    relation: Literal["supports", "refutes"]
    ordinal: int


@dataclass(frozen=True)
class PremiseRow(ValueRow):
    owner_key: str
    target: RecordKey


@dataclass(frozen=True)
class ConflictRow(ValueRow):
    pass


@dataclass(frozen=True)
class ConflictLink(ValueRow):
    conflict_key: str
    target: RecordKey


@dataclass(frozen=True)
class FieldBinding:
    pointer: str
    collection: str
    row_key: str
    column: str


@dataclass(frozen=True)
class StoredRecord:
    """һ��Դ���׼� D2 �м��ϣ����������� FactBatch blob��"""
    contract_version: str
    catalog_id: str
    sources: tuple[SourceRow, ...]
    entities: tuple[EntityRow, ...]
    facts: tuple[FactRow, ...]
    attributes: tuple[AttributeRow, ...]
    relations: tuple[RelationRow, ...]
    inventories: tuple[InventoryRow, ...]
    evidence: tuple[EvidenceRow, ...]
    evidence_links: tuple[EvidenceLink, ...]
    premises: tuple[PremiseRow, ...]
    conflicts: tuple[ConflictRow, ...]
    conflict_links: tuple[ConflictLink, ...]
    bindings: tuple[FieldBinding, ...]

