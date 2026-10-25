# 解析器注册接口协议（info-parser protocol）

本协议定义工具生产信息解析器的**注册方式、调用约定与错误返回**，供构造器
（`add-semantic-fact-constructor`）以本协议替换其实现阶段的占位桩。协议与实现
（`framework.py`）一致，任何调用行为均以此文档为准。

## 1. 注册方式

解析器按**工具标识**（tool id，即能力矩阵条目的 `producer_id`）注册，程序化注册：

```python
from info_parser.framework import registry, ParseResult

def my_parser(raw_output, profile) -> ParseResult:
    ...

registry.register("X-cargo_metadata", my_parser)
```

- 一个已接入的生产工具对应至少一个解析器；同一工具可注册一个解析器。
- 新增工具的解析器只增不改：仅调用 `register`，不修改框架与既有解析器（spec「解析器可增量接入」）。
- 未注册的工具标识在调用时得到「解析器未实现」的失败结果（见第 3 节）。

## 2. 调用约定

统一调用入口：

```python
result = registry.parse(tool_id, raw_output, profile=None) -> ParseResult
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `tool_id` | str | 工具标识（`producer_id`），用于发现解析器 |
| `raw_output` | 任意 | 工具的原生输出（文本 / JSON / 字典等） |
| `profile` | dict \| None | 调用剖面（含 `output_type`、`project_root` 等），按需传入 |

解析器函数签名为 `parser(raw_output, profile) -> ParseResult`，是**纯函数式确定性转换**
（相同输入恒得相同输出，无会话状态，design 决策 1）。

## 3. 错误返回

解析失败**不中断**，以结构化 `ParseFailure` 与数据项同型回传（design 决策 4）：

```python
ParseResult(
    items=[{...信息数据项...}],        # 成功/可解析部分产出的数据项（符合信息契约 schema）
    failure=ParseFailure(               # None 表示成功；非 None 表示失败或部分失败
        tool_id="X-cargo_metadata",     # 工具标识
        reason="...",                    # 失败原因
        unparsed=[...],                  # 不可解析部分清单（部分可解析时非空）
    ),
)
```

三种结果形态：

| 形态 | `items` | `failure` | 语义 |
|---|---|---|---|
| 成功 | 非空 | `None` | 全部可解析 |
| 失败 | 空 | 非 `None` | 无法解析，不产出数据项 |
| 部分可解析 | 非空 | 非 `None` | 可解析部分产出，不可解析部分进 `failure.unparsed` |

未注册工具：`registry.parse` 返回 `ParseFailure(reason="解析器未实现：<tool_id> 未注册")`，
不返回近似解析器（spec「解析器注册与发现」）。

解析器抛出的异常由框架捕获，统一转为 `ParseFailure(reason="解析异常：…")`，不向调用方
抛出（spec「解析失败显式表达」）。失败结果由构造器归并进 gaps，MUST NOT 编造、部分填充
或静默丢弃。

## 4. 输出契约

`items` 中的每项信息数据项 SHALL 符合信息契约机读 schema（`assets/schema/info-contract.schema.json`），
每条附源码证据定位（`evidence: {file, range}`），证据自工具输出可回溯、可在项目中定位。
