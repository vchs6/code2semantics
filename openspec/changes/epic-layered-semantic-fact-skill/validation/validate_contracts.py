"""Design-asset validation only; no product implementation or semantic proof."""
import copy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[4]
ASSETS = ROOT / "skills/layered-semantic-facts/assets"
HERE = Path(__file__).resolve().parent
schemas = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in ASSETS.glob("*.schema.json")}
for schema in schemas.values():
    Draft202012Validator.check_schema(schema)
registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())

def validate(schema_name, value):
    filename, _, fragment = schema_name.partition("#")
    schema = schemas[filename] if not fragment else {"$ref": schemas[filename]["$id"] + "#" + fragment}
    return list(Draft202012Validator(schema, registry=registry).iter_errors(value))

def expand(case):
    value = json.loads((HERE / case["fixture"]).read_text(encoding="utf-8"))
    for patch in case["patches"]:
        if patch["path"] == "":
            value = copy.deepcopy(patch["value"])
            continue
        keys = patch["path"].strip("/").split("/")
        target = value
        for key in keys[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        key = int(keys[-1]) if isinstance(target, list) else keys[-1]
        if patch["op"] == "delete":
            del target[key]
        else:
            target[key] = copy.deepcopy(patch["value"])
    return value

catalog = json.loads((ASSETS / "fact-catalog.json").read_text(encoding="utf-8"))
assert not validate("fact-catalog.schema.json", catalog)
report = (ROOT / catalog["research"]["path"]).read_text(encoding="utf-8").replace("\r\n", "\n")
assert hashlib.sha256(report.encode("utf-8")).hexdigest() == catalog["research"]["sha256"]
assert {f["id"] for f in catalog["fact_types"]} == {"F" + str(i) for i in range(1, 19)}
assert len({f["id"] for f in catalog["fact_types"]}) == len(catalog["fact_types"])
assert all(f["production_status"] == "unverified" for f in catalog["fact_types"])
assert {x["id"] for x in catalog["observation_granularities"]} == {"L1", "L2", "L3", "L4"}
assert {x["id"] for x in catalog["organization_axes"]} == {"O1", "O2", "O3", "O4", "O5"}
cases = json.loads((HERE / "schema-cases.json").read_text(encoding="utf-8"))
for case in cases:
    errors = validate(case["schema"], expand(case))
    assert bool(errors) != case["valid"], (case["name"], [e.message for e in errors])
semantic = json.loads((HERE / "semantic-cases.json").read_text(encoding="utf-8"))
for case in semantic:
    assert not validate("output-schema.schema.json", expand(case)), case["name"]
print(json.dumps({"schemas": len(schemas), "positive": sum(c["valid"] for c in cases), "negative": sum(not c["valid"] for c in cases), "semantic_cases_structurally_valid_not_runtime_verified": len(semantic), "catalog_facts": len(catalog["fact_types"]), "status": "design_assets_pass"}, ensure_ascii=False))
