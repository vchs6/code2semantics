"""Public design-asset checks. Does not execute product components or inspect source trees."""
import copy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[4]
ASSETS = ROOT / "skills/layered-semantic-facts/assets"
HERE = Path(__file__).resolve().parent
SCHEMAS = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in ASSETS.glob("*.schema.json")}
REGISTRY = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in SCHEMAS.values())

def shape_errors(name, value):
    filename, _, fragment = name.partition("#")
    schema = SCHEMAS[filename] if not fragment else {"$ref": SCHEMAS[filename]["$id"] + "#" + fragment}
    return [e.message for e in Draft202012Validator(schema, registry=REGISTRY).iter_errors(value)]

def expand(case):
    value = json.loads((HERE / case["fixture"]).read_text(encoding="utf-8"))
    for patch in case["patches"]:
        if not patch["path"]:
            value = copy.deepcopy(patch["value"])
            continue
        parts = patch["path"].strip("/").split("/")
        target = value
        for key in parts[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        key = int(parts[-1]) if isinstance(target, list) else parts[-1]
        if patch["op"] == "delete":
            del target[key]
        else:
            target[key] = copy.deepcopy(patch["value"])
    return value

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def node_key(node):
    return (node["source_id"], node["subject_id"], node["node_id"])

def premise_key(premise):
    return (*node_key(premise["node"]), premise["fact_id"], premise["field"])

def compatible(left, right):
    for key in left["environment"].keys() & right["environment"].keys():
        if left["environment"][key] != right["environment"][key]:
            return False
    known = {}
    for condition in left["conditions"] + right["conditions"]:
        if condition["state"] == "unknown":
            continue
        key = (condition["scope"], condition["expression"])
        if key in known and known[key] != condition["state"]:
            return False
        known[key] = condition["state"]
    return True

def semantic_errors(name, value):
    """Check supplied design fixtures, never fetch sources or implement a query loop."""
    errors = []
    def fail(code, message):
        errors.append(code + ": " + message)
    catalog = json.loads((ASSETS / "fact-catalog.json").read_text(encoding="utf-8"))
    fields = {f["id"]: f["fields"] for f in catalog["fact_types"]}
    # Cross-resource integrity that JSON Schema cannot express.
    for item in walk(value):
        if {"origin", "knowledge", "basis", "coverage", "validity"} <= item.keys():
            evidence = item["basis"]["evidence"]
            if item["knowledge"] == "supported":
                supports = any(e["relation"] == "supports" for e in evidence)
                if not supports and (item["origin"] == "observed" or not item["basis"]["premises"]):
                    fail("evidence", "supported assertion requires support, not only refutation")
            if item["knowledge"] == "absent":
                ids = {e["evidence_id"] for e in evidence if e["relation"] == "supports"}
                if not set(item["negative"]["check_evidence_ids"]) <= ids:
                    fail("evidence", "negative check evidence must resolve to supporting evidence")
                if item["negative"]["domain"] != item["coverage"]["domain"]:
                    fail("evidence", "negative domain must match checked coverage")
        if item.get("kind") == "cycle" and item["mode"] == "observed":
            if not any(e["relation"] == "supports" for e in item["execution_evidence"]):
                fail("evidence", "observed cycle requires supporting execution evidence")
            if not compatible({"environment":{},"conditions":item["joint_conditions"]}, {"environment":{},"conditions":[]}):
                fail("cycle", "mutually exclusive conditions cannot establish an observed cycle")
    def check_batch(batch, current_only=False, checks=(), authoritative_sources=None):
        sources = {}
        for source in batch["sources"]:
            if source["source_id"] in sources:
                fail("duplicate", "source identity")
            sources[source["source_id"]] = source
        if authoritative_sources is not None:
            current = {source["source_id"]: source for source in authoritative_sources}
            for source_id, source in sources.items():
                if (source_id not in current or current[source_id]["content_state"] != source["content_state"]
                    or current[source_id]["status"] != "available"):
                    fail("stale", "existing facts disagree with authoritative current source context")
            sources = current
        facts = batch.get("facts", batch.get("results", []))
        records = {}
        identities = set()
        for fact in facts:
            identity = (*node_key(fact["node"]), fact["fact_id"])
            if identity in identities:
                fail("duplicate", "fact identity")
            identities.add(identity)
            if fact["node"]["source_id"] not in sources:
                fail("reference", "fact source not declared")
            for field, assertion in fact["fields"].items():
                if field not in fields.get(fact["fact_type"], {}):
                    fail("catalog", "field outside catalog")
                records[(*identity, field)] = assertion
        for check in checks:
            key = premise_key(check["premise"])
            if key in records:
                fail("duplicate", "premise check duplicates a projected assertion")
            records[key] = check
        def check_current(assertion):
            if assertion["validity"]["state"] != "current":
                fail("stale", "non-current assertion in current result")
            for state in assertion["validity"]["sources"]:
                source = sources.get(state["source_id"])
                if not source or source["status"] != "available" or source["content_state"] != state["content_state"]:
                    fail("stale", "modified, missing or deleted source")
            for evidence in assertion["basis"]["evidence"]:
                source = sources.get(evidence["source_id"])
                if not source or source["status"] != "available" or source["content_state"] != evidence["content_state"]:
                    fail("stale", "evidence does not belong to current content")
        # All reference positions are source-qualified, including external observed_in.
        for item in walk(batch):
            if {"source_id", "subject_id"} <= item.keys() and item["source_id"] not in sources:
                fail("reference", "undeclared source on subject/node reference")
            if "source_ids" in item and any(source_id not in sources for source_id in item["source_ids"]):
                fail("reference", "context source is undeclared")
            if current_only and {"evidence_id", "source_id", "content_state", "relation"} <= item.keys():
                source = sources.get(item["source_id"])
                if not source or source["status"] != "available" or source["content_state"] != item["content_state"]:
                    fail("evidence", "evidence reference is not current or does not resolve")
            if current_only and {"knowledge", "basis", "validity"} <= item.keys():
                check_current(item)
        for check in checks:
            if current_only:
                check_current(check)
        visited = set()
        active = []
        def premises(key):
            if key in active:
                cycle = active[active.index(key):]
                if not any(any(e["relation"] == "supports" for e in records[k]["basis"]["evidence"]) for k in cycle):
                    fail("premise", "circular premises have no independent supporting evidence")
                return
            if key in visited:
                return
            active.append(key)
            assertion = records[key]
            for premise in assertion["basis"]["premises"]:
                target = premise_key(premise)
                record = records.get(target)
                if not record:
                    fail("premise", "necessary premise is unresolved")
                    continue
                states = {s["source_id"]: s["content_state"] for s in record["validity"]["sources"]}
                if (record["validity"]["state"] != "current" or record["knowledge"] not in ("supported", "absent")
                    or states.get(premise["node"]["source_id"]) != premise["content_state"]
                    or not compatible(assertion["context"], record["context"])):
                    fail("premise", "necessary premise is invalid, conflicting or context-incompatible")
                premises(target)
            active.pop()
            visited.add(key)
        # Inventory/navigation assertions carry the same necessary-premise obligations as fields.
        for index, assertion in enumerate(walk(batch)):
            if {"origin", "knowledge", "basis", "validity"} <= assertion.keys() and not any(assertion is a for a in records.values()):
                records[("@assertion", index)] = assertion
        for key in list(records):
            if current_only or records[key]["validity"]["state"] == "current":
                premises(key)
        for conflict in batch["conflicts"]:
            for member in conflict["members"]:
                if premise_key(member) not in records:
                    fail("reference", "conflict member does not resolve")
        return records
    if name.startswith("pipeline.schema.json"):
        kind = value.get("kind")
        if kind in ("construct_result", "induction_result", "stored_record"):
            check_batch(value["batch"])
        elif kind in ("construct_request", "induction_request"):
            authoritative = value["current_source_context"]["sources"] if kind == "construct_request" else None
            check_batch(value["existing_valid_facts"], True, authoritative_sources=authoritative)
        elif kind == "read_result":
            check_batch(value["known"], True)
    if name == "output-schema.schema.json":
        query = value["query"]
        check_batch(value, True, value["premise_checks"])
        selected = {}
        for selection in query["selections"]:
            selected.setdefault(selection["fact_type"], set()).update(selection["fields"])
        outside = {(o["fact_type"], f) for o in value["out_of_catalog"] for f in o["fields"]}
        expected_outside = {(t, f) for t, fs in selected.items() for f in fs if f not in fields.get(t, {})}
        if outside != expected_outside:
            fail("catalog", "out-of-catalog list differs from requested unknown fields")
        target = query["target"]
        children = set()
        inventory_complete = False
        matching = []
        for inv in value["direct_nodes"]:
            if inv["target"] != target or inv["granularity"] != query["granularity"]:
                fail("projection", "only the requested direct boundary may be projected")
            else:
                matching.append(inv)
                a = inv["assertion"]
                inventory_complete = (a["knowledge"] == "supported" and a["coverage"]["completeness"] == "complete")
                children.update(node_key(n) for n in inv["children"])
        if len(matching) != 1:
            fail("incomplete", "exactly one direct boundary inventory is required")
        allowed_nodes = children | ({node_key(target["node"])} if target["kind"] == "node" else set())
        found = set()
        for fact in value["results"]:
            if node_key(fact["node"]) not in allowed_nodes or query["granularity"] not in fact["granularities"]:
                fail("projection", "unrequested node or granularity")
            for field, assertion in fact["fields"].items():
                if field not in selected.get(fact["fact_type"], set()):
                    fail("projection", "unrequested field")
                if assertion["knowledge"] in ("supported", "absent"):
                    if target["kind"] == "scope" or fact["node"] == target["node"]:
                        found.add((node_key(fact["node"]), fact["fact_type"], field))
                elif not any(g["fact_type"] == fact["fact_type"] and field in g["fields"] for g in value["gaps"]):
                    fail("unsatisfied", "insufficient assertion must retain an explicit gap")
        if not inventory_complete:
            if value["termination"] == "satisfied":
                fail("incomplete", "incomplete direct nodes cannot satisfy request")
            if not any(g["reason"] == "coverage_incomplete" for g in value["gaps"]):
                fail("incomplete", "missing direct-node completeness gap")
        requested = {(t, f) for t, fs in selected.items() for f in fs} - expected_outside
        requested_nodes = children if target["kind"] == "scope" else {node_key(target["node"])}
        obligations = {(node, fact_type, field) for node in requested_nodes for fact_type, field in requested}
        if value["termination"] == "satisfied":
            if value["gaps"] or outside or not obligations <= found:
                fail("unsatisfied", "request has unresolved fields or gaps")
        elif obligations - found and not value["gaps"]:
            fail("unsatisfied", "termination must preserve remaining in-catalog gaps")
    return errors

def validate(name, value):
    return shape_errors(name, value) or semantic_errors(name, value)

def main():
    by_id = {schema["$id"]: schema for schema in SCHEMAS.values()}
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
        for item in walk(schema):
            if "$ref" in item:
                uri, _, pointer = item["$ref"].partition("#")
                target = by_id[uri] if uri else schema
                for key in pointer.strip("/").split("/") if pointer else []:
                    target = target[key.replace("~1", "/").replace("~0", "~")]

    catalog = json.loads((ASSETS / "fact-catalog.json").read_text(encoding="utf-8"))
    assert not shape_errors("fact-catalog.schema.json", catalog)
    report = (ROOT / catalog["research"]["path"]).read_text(encoding="utf-8").replace("\r\n", "\n")
    assert hashlib.sha256(report.encode()).hexdigest() == catalog["research"]["sha256"]
    assert {f["id"] for f in catalog["fact_types"]} == {"F" + str(i) for i in range(1, 19)}
    assert len(catalog["fact_types"]) == 18
    assert {g["id"] for g in catalog["observation_granularities"]} == {"L1", "L2", "L3", "L4"}
    assert {g["id"] for g in catalog["organization_axes"]} == {"O1", "O2", "O3", "O4", "O5"}
    common = SCHEMAS["common.schema.json"]["$defs"]
    assert set(catalog["assertion_envelope"]) == set(common["assertion"]["required"])
    branches = {b["if"]["properties"]["fact_type"]["const"]: b["then"]["properties"]["fields"]["properties"] for b in common["fact_node"]["allOf"]}
    for fact in catalog["fact_types"]:
        assert set(branches[fact["id"]]) == set(fact["fields"])
        for field, definition in fact["fields"].items():
            assert definition["basis"]
            assert branches[fact["id"]][field]["allOf"][1]["properties"]["value"]["$ref"].endswith("/" + definition["value_shape"])

    assert all("production_status" not in f for f in catalog["fact_types"])
    cases = json.loads((HERE / "schema-cases.json").read_text(encoding="utf-8"))
    for case in cases:
        errors = shape_errors(case["schema"], expand(case))
        assert bool(errors) != case["valid"], (case["name"], errors)
        if case["valid"]:
            assert not semantic_errors(case["schema"], expand(case)), case["name"]
    semantic = json.loads((HERE / "semantic-cases.json").read_text(encoding="utf-8"))
    for case in semantic:
        value = expand(case)
        assert not shape_errors(case["schema"], value), (case["name"], "semantic case must be shape-valid")
        errors = semantic_errors(case["schema"], value)
        assert bool(errors) != case["valid"], (case["name"], errors)
        if not case["valid"] and case.get("expected_code"):
            assert any(e.startswith(case["expected_code"] + ":") for e in errors), (case["name"], errors)
    print(json.dumps({"schemas":len(SCHEMAS),"shape_cases":len(cases),"semantic_cases":len(semantic),"catalog_facts":18,"status":"design_assets_pass","runtime_verified":False}))

if __name__ == "__main__":
    main()
