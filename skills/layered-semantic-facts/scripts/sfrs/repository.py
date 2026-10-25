"""SFRS 仓库实现（任务 4.1–4.5）：Python + SQLite（design 决策 9）。

- DDL 依据 design OQ1 回填结论（research/storage-survey.md）：三表实体粒度布局
  （entities/attributes/relations），属性为 EAV 行，覆盖索引 + 关系双向索引，
  CREATE TABLE IF NOT EXISTS 幂等建库。
- 结构校验以机读 schema（assets/schema/sfrs.schema.json）为唯一依据；提交（含批量）
  为原子生效单元；同 ID 同内容幂等、不同内容判版本冲突（spec 增量维护/结构校验）。
- 版本由调用方给定；检索要求显式版本参数（OQ3 保守语义）。
- 仓库只存来源标注，不存源码；不判断事实语义正确性（spec 结构校验及其边界）。
"""
import hashlib
import json
import os
import sqlite3
from pathlib import Path

import jsonschema

from layout import SKILL_ROOT, resolve_asset
from sfrs.model import decompose, reassemble

_SCHEMA_PATH = resolve_asset(SKILL_ROOT, "schema") / "sfrs.schema.json"


def _default_db_path():
    env = os.environ.get("SFRS_DB_PATH")
    if env:
        return Path(env)
    return Path.home() / ".atomcode" / "sfrs" / "facts.db"  # OQ4 保守缺省


DDL = """
CREATE TABLE IF NOT EXISTS entities (
  project       TEXT NOT NULL,
  version       TEXT NOT NULL,
  entity_id     TEXT NOT NULL,
  fact_type     TEXT NOT NULL,
  layer         TEXT NOT NULL,
  evidence_file TEXT,
  evidence_range TEXT,
  content_hash  TEXT NOT NULL,
  PRIMARY KEY (project, version, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_entities_type
  ON entities(project, version, fact_type, entity_id);
CREATE TABLE IF NOT EXISTS attributes (
  project   TEXT NOT NULL,
  version   TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  name      TEXT NOT NULL,
  value     TEXT NOT NULL,
  PRIMARY KEY (project, version, entity_id, name),
  FOREIGN KEY (project, version, entity_id)
    REFERENCES entities(project, version, entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_attr_lookup
  ON attributes(project, version, name, value, entity_id);
CREATE TABLE IF NOT EXISTS relations (
  project       TEXT NOT NULL,
  version       TEXT NOT NULL,
  relation_id   TEXT NOT NULL,
  from_entity   TEXT NOT NULL,
  to_entity     TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  PRIMARY KEY (project, version, relation_id),
  FOREIGN KEY (project, version, from_entity)
    REFERENCES entities(project, version, entity_id) ON DELETE CASCADE,
  FOREIGN KEY (project, version, to_entity)
    REFERENCES entities(project, version, entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rel_from ON relations(project, version, from_entity);
CREATE INDEX IF NOT EXISTS idx_rel_to ON relations(project, version, to_entity, relation_type);
"""


def _content_hash(entity):
    payload = {k: entity.get(k) for k in ("fact_type", "layer", "fields", "evidence")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


class SFRS:
    """语义事实仓库（Skill 专用直连，design 决策 8：单写者本地组件）。"""

    def __init__(self, db_path=None):
        self._db_path = Path(db_path) if db_path else _default_db_path()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.executescript(DDL)  # 幂等建库
        self._conn.commit()
        schema = json.loads(_SCHEMA_PATH.read_text("utf-8"))
        self._resolver = jsonschema.RefResolver.from_schema(schema)
        self._fact_set_validator = jsonschema.Draft7Validator(schema)
        self._entity_validator = jsonschema.Draft7Validator(
            schema["definitions"]["entity"], resolver=self._resolver)
        self._relation_validator = jsonschema.Draft7Validator(
            schema["definitions"]["relation"], resolver=self._resolver)

    def accessible(self):
        return True  # 文件型仓库：建库即可达

    # ---- 提交（结构校验 + 原子生效） --------------------------------------

    def submit(self, fact_set):
        """提交语义事实集（读写单位）。结构校验 → 实体分解 → 原子写入。

        返回 {"accepted": 新入库实体数}；校验失败/版本冲突返回 {"error": 原因}
        且仓库状态不变（拒绝不生效）。
        """
        errors = sorted(self._fact_set_validator.iter_errors(fact_set),
                        key=lambda e: list(e.absolute_path))
        if errors:
            first = errors[0]
            loc = "/".join(str(p) for p in first.absolute_path) or "<root>"
            return {"error": f"读写单位须为符合机读 schema 的语义事实集 [{loc}]: {first.message}"}
        project, version = fact_set["project"], fact_set["version"]
        entities = decompose(fact_set)
        accepted = 0
        try:
            for e in entities:
                result = self._insert_entity(project, version, e)
                if "error" in result:
                    self._conn.rollback()
                    return result
                accepted += result["accepted"]
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return {"accepted": accepted}

    def _insert_entity(self, project, version, entity):
        """单实体写入（调用方管理事务）。幂等/冲突判定按同 (项目,版本,实体ID)。"""
        eid = entity["entity_id"]
        h = _content_hash(entity)
        row = self._conn.execute(
            "SELECT content_hash FROM entities WHERE project=? AND version=? AND entity_id=?",
            (project, version, eid)).fetchone()
        if row is not None:
            if row[0] != h:
                return {"error": (f"版本冲突：实体 {eid} 在同（项目、版本）内已存在"
                                  f"且内容不同，已存事实保持不变")}
            return {"accepted": 0}  # 同 ID 同内容 → 幂等
        ev = entity.get("evidence") or {}
        self._conn.execute(
            "INSERT INTO entities (project, version, entity_id, fact_type, layer,"
            " evidence_file, evidence_range, content_hash) VALUES (?,?,?,?,?,?,?,?)",
            (project, version, eid, entity["fact_type"], entity["layer"],
             ev.get("file"), ev.get("range"), h))
        for name, value in (entity.get("fields") or {}).items():
            self._conn.execute(
                "INSERT INTO attributes (project, version, entity_id, name, value)"
                " VALUES (?,?,?,?,?)",
                (project, version, eid, name, json.dumps(value, ensure_ascii=False)))
        return {"accepted": 1}

    def submit_entities(self, project, version, entities):
        """批量提交实体（校验 → 原子生效）。"""
        for e in entities:
            if list(self._entity_validator.iter_errors(e)):
                first = next(self._entity_validator.iter_errors(e))
                return {"error": f"实体结构不符 [{first.absolute_path}]: {first.message}"}
        accepted = 0
        try:
            for e in entities:
                result = self._insert_entity(project, version, e)
                if "error" in result:
                    self._conn.rollback()
                    return result
                accepted += result["accepted"]
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return {"accepted": accepted}

    def submit_relations(self, project, version, relations):
        """批量提交显式关系（校验结构 + 引用有效性 → 原子生效）。"""
        for r in relations:
            if list(self._relation_validator.iter_errors(r)):
                first = next(self._relation_validator.iter_errors(r))
                return {"error": f"关系结构不符 [{first.absolute_path}]: {first.message}"}
        for r in relations:
            for end in (r["from_entity"], r["to_entity"]):
                row = self._conn.execute(
                    "SELECT 1 FROM entities WHERE project=? AND version=? AND entity_id=?",
                    (project, version, end)).fetchone()
                if row is None:
                    return {"error": (f"引用无效：关系 {r['relation_id']} 的实体"
                                      f" {end} 在（项目、版本）内不存在")}
        try:
            for r in relations:
                self._conn.execute(
                    "INSERT OR IGNORE INTO relations (project, version, relation_id,"
                    " from_entity, to_entity, relation_type) VALUES (?,?,?,?,?,?)",
                    (project, version, r["relation_id"], r["from_entity"],
                     r["to_entity"], r["relation_type"]))
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return {"accepted": len(relations)}

    def invalidate(self, project, version, entity_id):
        """显式失效：删除该（项目、版本）内的实体及其属性（事实随新版本表达新状态）。"""
        self._conn.execute("DELETE FROM entities WHERE project=? AND version=? AND entity_id=?",
                           (project, version, entity_id))
        self._conn.commit()
        return {"invalidated": entity_id}

    # ---- 读取与查询 -------------------------------------------------------

    def read(self, project, version):
        """按（项目、版本）取回语义事实集；该版本无事实返回 None。"""
        if not version:
            raise ValueError("检索要求显式版本参数（不设缺省版本语义，design OQ3）")
        rows = self._conn.execute(
            "SELECT entity_id, fact_type, layer, evidence_file, evidence_range"
            " FROM entities WHERE project=? AND version=? ORDER BY rowid",
            (project, version)).fetchall()
        if not rows:
            return None
        entities = []
        for eid, fact_type, layer, efile, erange in rows:
            attrs = self._conn.execute(
                "SELECT name, value FROM attributes"
                " WHERE project=? AND version=? AND entity_id=? ORDER BY rowid",
                (project, version, eid)).fetchall()
            entity = {"entity_id": eid, "fact_type": fact_type, "layer": layer,
                      "fields": {name: json.loads(value) for name, value in attrs},
                      "evidence": {"file": efile, "range": erange}}
            entities.append(entity)
        return reassemble(entities, project=project, version=version)

    def query(self, project, version, fact_type=None, entity_id=None):
        """按范围精确查询：只返回匹配条件的实体记录（不强迫读取完整模型）。"""
        if not version:
            raise ValueError("检索要求显式版本参数（不设缺省版本语义，design OQ3）")
        sql = ("SELECT entity_id, fact_type, layer, evidence_file, evidence_range"
               " FROM entities WHERE project=? AND version=?")
        params = [project, version]
        if fact_type is not None:
            sql += " AND fact_type=?"
            params.append(fact_type)
        if entity_id is not None:
            sql += " AND entity_id=?"
            params.append(entity_id)
        sql += " ORDER BY rowid"
        rows = self._conn.execute(sql, params).fetchall()
        result = []
        for eid, ft, layer, efile, erange in rows:
            attrs = self._conn.execute(
                "SELECT name, value FROM attributes"
                " WHERE project=? AND version=? AND entity_id=? ORDER BY rowid",
                (project, version, eid)).fetchall()
            result.append({"entity_id": eid, "fact_type": ft, "layer": layer,
                           "fields": {n: json.loads(v) for n, v in attrs},
                           "evidence": {"file": efile, "range": erange}})
        return result

    def relations_from(self, project, version, entity_id):
        """沿显式关系遍历：只返回 Skill 提交的关系边，不推导新事实。"""
        rows = self._conn.execute(
            "SELECT relation_id, from_entity, to_entity, relation_type"
            " FROM relations WHERE project=? AND version=? AND from_entity=? ORDER BY rowid",
            (project, version, entity_id)).fetchall()
        return [{"relation_id": rid, "from_entity": f, "to_entity": t,
                 "relation_type": rt} for rid, f, t, rt in rows]
