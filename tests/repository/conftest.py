"""ͬԴ���� fixture������ȡԴ��Ŀ����֤���������塣"""
import json
import sys
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "skills/layered-semantic-facts/assets"
sys.path.insert(0, str(ROOT / "skills/layered-semantic-facts/scripts"))

@pytest.fixture
def schema_root():
    return ASSETS

@pytest.fixture
def batch():
    return json.loads((Path(__file__).parent / "fixtures/full-batch.json").read_text(encoding="utf-8"))

@pytest.fixture
def public_validator(schema_root):
    schemas = [json.loads(p.read_text(encoding="utf-8")) for p in schema_root.glob("*.schema.json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    return Draft202012Validator({"$ref": "https://code2semantics.local/schema/pipeline.schema.json#/$defs/fact_batch"}, registry=registry)

@pytest.fixture
def codec(schema_root):
    from semantic_facts.repository.contract import ContractCodec
    return ContractCodec(schema_root)

@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "facts.db"

