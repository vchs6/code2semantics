# SFRS 使用文档（Skill 专用调用入口，任务 4.6）

服务形态：**进程内 Python 接口**（design 决策 8：Skill 专用直连，单写者本地组件；无网络服务）。
落盘位置：单文件 SQLite 数据库，位置经环境变量 `SFRS_DB_PATH` 指定，缺省 `~/.atomcode/sfrs/facts.db`（design OQ4 回填结论）。

## 接入方式（Skill 查询流程）

编排器对仓库的调用面为三个方法（与内存桩同构，SFRS 落地后仅替换适配层）：

```python
import sys
sys.path.insert(0, "scripts")           # Skill 根下的 scripts/（或经 layout.register_skill_paths()）

from sfrs.repository import SFRS

repo = SFRS()                            # 使用 SFRS_DB_PATH 或缺省落盘位置
repo.accessible()                        # -> True（文件型仓库，建库即可达）

# 提交：读写单位为语义事实集（结构以 assets/schema/sfrs.schema.json 为权威校验）
result = repo.submit({"project": "indicatif", "version": "a65379f…", "facts": {…}})
# -> {"accepted": 新入库实体数}；校验失败/版本冲突 -> {"error": 可定位原因}，仓库状态不变

# 读取：显式版本参数（不设缺省版本语义）；该版本无事实返回 None
fact_set = repo.read("indicatif", "a65379f…")

# 精确查询与关系遍历（可选，供 Skill 按需取回）
rows = repo.query(project="indicatif", version="a65379f…", fact_type="入口")
edges = repo.relations_from("indicatif", "a65379f…", entity_id)
```

## 行为要点

- 提交（含批量）为**原子生效单元**：任一变更不合规则整体不生效，仓库状态不变；
- 同（项目、版本）内同 ID 同内容**幂等**（不产生重复事实），同 ID 不同内容判**版本冲突**拒绝；
- 事实按（项目、版本）持久化，历史版本可追溯取回；仓库长期保留全部版本；
- 仓库只存来源标注（文件:行号范围），不存源码、不校验源码可达性、不判断事实语义正确性。
