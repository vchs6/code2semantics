# 最小事实集响应契约（output-schema）

契约查询模式的输出为机器可读 JSON 事实集。本 schema 定义其结构；层级与字段以 `fact-catalog.md` 为准。机读权威为 `assets/schema/output.schema.json`（JSON Schema，语言无关，单一权威副本）；本文件为其人读说明，二者字段须一致。

## 结构

```json
{
  "project": "<项目存储位置>",
  "project_defaulted": true,
  "repository_defaulted": true,
  "version": "<真实版本标识>",
  "version_fallback": false,
  "facts": {
    "<层级>": [
      {
        "type": "<事实类型>",
        "fields": { "<字段>": "<值>", "...": "..." },
        "evidence": { "file": "<路径>", "range": "<起止行号>" }
      }
    ]
  },
  "gaps": [
    { "type": "<事实类型>", "reason": "<未满足原因>" }
  ],
  "out_of_scope": ["<目录外引用的事实类型>", "..."]
}
```

## 字段说明

- `project`：实际使用的项目根；`project_defaulted` 为 `true` 时表示采用了宿主当前工作目录缺省。
- `repository_defaulted`：为 `true` 时表示事实仓库位置采用了缺省来源（环境变量或固定路径）。
- `version`：真实版本标注——本事实集对应的来源项目版本（Git commit 或本地指纹）；`version_fallback` 为 `true` 时表示请求版本缺失、已回退至当前版本（MUST NOT 以当前版本冒充请求版本）。
- `facts`：分层事实集，仅含契约要求的层与字段（最小化）；每条事实 `evidence` 提供源码证据定位（文件与行号范围）。
- `gaps`：目录内但项目中缺失/无法提取的事实，含原因；MUST NOT 编造填充。
- `out_of_scope`：契约引用了目录外事实，显式声明，不产生对应事实内容。

## 约束

- 只包含契约要求的层与字段；契约未要求的信息 MUST NOT 出现。
- 目录外引用与 gaps 分列声明，不得混同。
- 每条事实可溯源：`evidence` 指向真实存在的源码位置。

## 与报告模板的一致性

人可读报告（`report-template.md`）从本事实集生成（单一事实源），字段一一对应，仅呈现形式不同。
