# 查询契约

本工件在 fact-catalog 之后派生；依据报告§3 R1/R2/R15/R16、§5 O1/O5、§6 F1/F2/F17/F18 与§8 S1–S12。机读权威是 `../assets/contract-format.schema.json`，复用 common.schema.json；版本 1.0.0，目录 semantic-facts-20261025。

`scope` 当前模式缺省时由宿主当前工作目录补为 directories 并在响应标注；目录集合只是观察入口。source namespace 由源注册表绑定独立来源身份，不能取文件名/行号或最近父目录来合并主体。当前模式先捕获全部授权内容清单（含已修改、未跟踪、排除规则和配置），再按不可变内容快照执行。历史模式必须指明 saved scope 和各来源快照，读取保存证据，不读取当前路径替代历史。无法取得历史内容时明确 gap。

target 为 scope 入口、确切 node continuation 或显式 refresh 节点；selections 指定事实类型与非空字段集合。目录外类型/字段为 out_of_catalog；合法目录内的未满足项为 gaps；二者可同时返回。结构合法但未知节点、无效主体或过期引用不成为空成功，返回 invalid_reference/stale_snapshot gap。版本/目录标识不匹配是输入错误，禁止当缓存命中。

一次仅返回目标的直接属性及下一级事实节点；更深节点只给 continuation 与身份/可靠性元数据，不递归展开。节点没有固定父字段，children 表达本次导航路径而非全局身份树。scope 可直接进入任何粒度；请求不自动扩大源码授权。

continuation 精确绑定 node、snapshot_set_id 与 fact_revision。current 续查先比较实际来源快照集合，变化时报 stale_snapshot；不能静默跟随新版本。historical 续查固定原集合和原 revision。精确 node 续查只读指定 fact_revision，不调用构造；缺字段即返回目标明确的 gap。显式 refresh 仅用于current模式且必须匹配同一来源快照集合，读取该节点最新知识并允许按缺口构造新revision，响应 resolved_target 给出新continuation。历史模式及所有精确node请求均只读；scope历史请求读取指定源码快照内查询开始时的已存知识并标出实际revision，不构造。相同源码快照内新证据形成新fact_revision，不覆盖旧引用；源码变动仍先报stale_snapshot，需新的scope查询重新解析主体，不自动改绑refresh引用。跨来源任一版本变化都重审依赖它的断言。

JSONSchema只检查输入结构、值类型及局部条件，不能验证目录成员、引用存在、命名域注册、快照内容、同一性、授权范围或依赖闭包；运行校验职责见 runtime-contracts.md。查询模式总返回 JSON；自然语言模式先补同一契约，意图不足先澄清。报告只在明确请求时由宿主从该响应渲染。
