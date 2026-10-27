---
name: project-bringup
description: >-
  基于 BASE 产品克隆 HMOS 新项目并做硬件适配。Phase1：全平台克隆挂接。
  Phase2：多平台同一流程（读飞书文档→比差异→计划确认→按仓库实文件适配）；
  表样式与代码落点实时识别，细节见各平台 profile。
  Phase3：按飞书 Bringup 报告模板导出（【自动】填满，【人工】留空）。
disable-model-invocation: true
---

# HMOS 项目 Bringup

从 **BASE** 派生 **NEW**。只按本 Skill 执行。

| 步骤 | 内容 | 状态 |
| --- | --- | --- |
| Phase 1 | 复制 BASE→NEW 并挂接编译/配置 | **已实现**（apollo5 / mhs003 / mhs003s） |
| Phase 2 | 硬件表适配器件、GPIO | **同一流程**；平台差异仅在落点与代码格式（见 profile） |
| Phase 3 | 导入报告 + 生成 bringup 飞书文档 | **模板已就绪**；复制母版后再填，勿改母版 |

未实现的能力禁止假装完成。

## 原理

产品绑定：

1. **目录** `platform/board/<platform>/products/<name>`，由 `HMI_PRODUCT_CUSTOMIZE_DIR` 选中
2. **板型** `HMI_BOARD_<PREFIX>_<NAME_UPPER>`（`Config.in` choice + default）
3. **defconfig / 条件编译 / 资源名** 打开该板型，并挂接共享代码与资源

| 平台 | 板型前缀 | 主 defconfig |
| --- | --- | --- |
| `mhs003` | `HMI_BOARD_MHS003_` | `mhs003_<new>_defconfig` |
| `mhs003s` | `HMI_BOARD_MHS003S_` | `mhs003s_<new>_defconfig` |
| `apollo5` | `HMI_BOARD_APOLLO330P_` | `apollo330_<new>_defconfig` |

细则：[profiles/apollo5.md](profiles/apollo5.md) · [profiles/mhs003.md](profiles/mhs003.md) · [profiles/mhs003s.md](profiles/mhs003s.md)

通用规则：先 dry-run/列出变更再 apply；默认不 commit；文件清单按 BASE **动态发现**，不写死白名单。Phase1 不改 PNP/广播名/pin 数值。

**Skill 管范围和流程，不维护、不限定器件型号。** 任何型号→配置都按该行 NEW 型号在**当前仓库**搜已有写法；profile 只给路径/格式起点，禁止把 profile 或历史项目当成器件白名单。

**关键**：飞书硬件模板 **只服务 Phase2**，不能单独「新建项目」。新建 = Phase1 脚本 → 再填模板做 Phase2。

---

## Phase 1

锁定：`平台`、`仓库根`、`base`、`new`。`--new` = 硬件表 §1 NEW **原文**（大小写、连字符均保留）。禁止为「符合小写惯例」而改拼写。板型宏 = 前缀 + NEW.upper()。

在本 Skill 目录执行：

```bash
python3 scripts/phase1_clone_product.py \
  --repo-root <HMOS_ROOT> --platform <apollo5|mhs003|mhs003s> \
  --base <base> --new <new> --dry-run
```

确认后去掉 `--dry-run`。命令见 [examples.md](examples.md)。

校验（**以仓库为准**，表上「Phase1 已完成」不能替代）：`products/<new>`、主 defconfig、`Config.in` 含新板型符号；有 `.repo/manifests` 时同步复制产品 xml（文件名/内容可自动；远程 git 分支仍须 CI/架构师创建）。

---

## Phase 2 — 器件 / GPIO

三平台走同一套流程。平台差异只在表样式、代码路径和宏/脚名格式（见下表）。

不变的总流程：

**读表 → 比较差异 → 出变更计划 → 用户确认 → 按当前代码格式适配 → 校验**

禁止把「有没有单独写回 .py」当成能力缺口；落码由 Agent 按计划改仓库即可。解析优先用/扩展 `scripts/phase2_gpio_diff.py`，禁止每次从零新写一份解析脚本（除非现脚本无法扩展）。

| 变的是什么 | 怎么处理 |
| --- | --- |
| GPIO / 器件表样式 | **实时识别**表头、脚标识、产品列（示例表仅供参考） |
| 代码路径、宏/脚名格式 | 按平台查 profile「落点」；**以仓库实文件为准**，路径/文件名变了就按现仓库找，不硬套旧名 |
| 器件型号→配置 | 不查型号名单。`SKILL配置=是` 时用该行 NEW 型号在仓库搜已有写法；搜不到或互相冲突 → 待定 |

### 数据输入（飞书）

[项目Bringup硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（以线上当前结构为准）。**黄格=必填**，无黄底=选填。模板含填写规范与示例，**不含**识别/写回流程。读飞书用 Windows `cmd.exe` + `lark-cli`。

| 节 | 必读字段（黄格） | 选填 | Agent |
| --- | --- | --- | --- |
| §0 | —（规范给人看） | — | 语义以本节「规则」为准 |
| §1 | 平台 / BASE / NEW / Phase1 状态 | — | 必读；NEW 原文锁定身份 |
| §2 | GPIO 链接、BASE/NEW 列名、`GPIO·SKILL配置` | 工作表名 | 必读；多 sheet 且自动选不唯一 → 停，补工作表名 |
| §3 | **器件类型**、BASE **型号**、NEW **型号**、`SKILL配置` | 供别、备注（厂家） | 逐行读；厂家不参与映射 |
| §4 | 状态均为「完成」 | — | 任一项未完成 → 停 |

### 规则（强制）

| 条件 | 行为 |
| --- | --- |
| 仓库缺少 `products/<NEW>` / 主 defconfig / Config.in 板型 | **禁止** Phase2 写回（即使表勾了 Phase1 已完成） |
| §1 Phase1≠已完成，或 §4 有「未完成」 | **禁止**做 Phase2 写回；先 Phase1 / 补表 |
| §1/§2/§3 必填黄格缺失或型号空泛（如只写「电源芯片」） | **停**，请用户补齐后再出计划 |
| **未获用户确认变更清单** | **禁止改仓库任何文件**；只允许读表、分析、输出计划 |
| 同一器件多行（一供/二供等） | **逐行**比较型号与 `SKILL配置`，分别写入计划 |
| 器件 BASE 型号 = NEW 型号（或 NEW 为「同左」） | **禁止改**该器件；按仅检查 |
| NEW 为「无」/「（无…）」等且 BASE 有型号 | 视为型号变更（相对 BASE 去掉或换方案），按 `SKILL配置` 处理 |
| 器件 `SKILL配置` 空 | BASE=NEW（或同左）→ 仅检查；BASE≠NEW → 按否 |
| 器件 `SKILL配置=否` | **禁止自动适配**；计划里记「仅报告」 |
| 器件 `SKILL配置=是` | 用该行 NEW 型号在仓库搜已有写法（见下「器件落码」）；无映射或冲突 → 待定，确认后仍不瞎改 |
| 仓库里 BASE 与 NEW 对应**彼此独立**的配置项（可同时为 y） | 计划标 **需拍板**：只开 NEW / 双开 / 只留 BASE；**禁止默认关 BASE 对应项** |
| `GPIO·SKILL配置=否` | 计划只含差异清单，确认后仍不改码 |
| `GPIO·SKILL配置=是` | 计划含拟改文件/脚；用户确认后再按仓库实格式写回 |
| 备注/厂家 | 可展示，**不参与**映射判断 |
| 始终 | 不改板型符号、`HMI_PRODUCT_CUSTOMIZE_DIR`、BASE 产品树 |

### 步骤（强制：计划 → 确认 → 再改码）

投喂 [硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（或同结构副本）后：

1. **读 §1 / §4**：平台、base、new、Phase1、确认状态；校验必填黄格齐全。**仓库**确认 `products/<NEW>` + 主 defconfig + `Config.in` 板型存在（表勾选不能替代）。
2. **分析 §2 GPIO + §3 器件**（只读不写）：GPIO 动态出差异并分类；器件 **逐行**（含一供/二供）按规则分类。在仓库中定位当前落点与代码格式（见下表与 profile）。整理成 **变更计划**（需拍板项单列）。
3. **停下来请用户确认**：展示计划；问清范围。**未明确同意前禁止改代码。**
4. **用户确认后**再执行适配（仅确认范围内的项，含用户附加的拍板结论）；映射不到的项保持待定并说明。
5. **校验**：实际改动与确认范围一致；板型/CUSTOMIZE_DIR 未误改。

用户可回复例如：`确认全部` / `确认全部，<对需拍板项的结论>` / `只改器件，GPIO 先不动` / `取消`。确认范围外的需拍板项保持待定。

### 计划输出格式（确认前必须给出）

| 类别 | 每条写清 |
| --- | --- |
| 器件 | 类型、供别（若有）、BASE→NEW **型号**、`SKILL配置`、拟动作（含仓库对照来源）；备注/厂家可附带但不作依据 |
| GPIO | 脚标识、BASE信号→NEW信号、**功能搬脚 / 仅清单**、拟改文件、不确定项 |
| 需拍板 | 独立配置项开法、UART 成对脚与表字面相反、overlay 来源等，必须等人拍板才改 |
| 风险 / 不做 | 必填缺失、无映射、`SKILL配置=否` |

### GPIO：固定流程 + 动态识别（强制）

两段式（缺一段都不算 Phase2 GPIO 做完）；落码必须在用户确认计划之后：

1. **解析**：动态认表 → 对齐 BASE/NEW 列 → 出差异清单（与平台无关）→ **写入变更计划**。
2. **落码**（仅确认后）：在 `platform/board/<平台>/products/<new>/` 等处 **实时找到** GPIO 定义文件与现有写法，按差异改；找不到或对不上格式 → 标待定，不编造。

模板/文档里的表示例 **只是样例**，不绑定某平台只能用某例。Agent **禁止**按「必须是例1/2/3」硬套。

| 步 | 做什么 | 要点 |
| --- | --- | --- |
| 1 | 取用户 §2 链接 | `drive +inspect`：电子表格则 `+export xlsx`；文档才 `docs +fetch`。fetch 失败禁止改猜内容 |
| 2 | 定位「产品矩阵」表 | 多 sheet 必须能唯一确定（`--sheet` 或 §2 工作表名）。自动选不唯一 / 空表头伪匹配 → **停**，列出候选页 |
| 3 | 发现表头行 | 含产品列名的那一行（不假设第 0 行）；空表头不得当产品列 |
| 4 | 发现脚标识列 | 动态认 `PIN Name` / `Pin` / `Pad` / `GPIO` / `Net` / 「脚名」等；可多列；跳过 Function/描述/Type |
| 5 | 对齐 BASE/NEW 列 | 用 §2 列名模糊匹配；对不上就停并列出实际表头，禁止猜 |
| 6 | 逐行 diff | 只保留 BASE信号 ≠ NEW信号；再分成 **功能搬脚** vs **仅清单**（去括号/EINT/空白后主体相同） |
| 7 | 纳入变更计划 | 功能搬脚拟改文件；仅清单不改码；`GPIO·SKILL配置=否` 则全部不改码 |
| 8 | 用户确认后落码 | 仅已确认项；按仓库现格式写。成对脚与 overlay 规则见下 |

解析必须带 `--explain`，确认所选 sheet 名后再写计划。

```bash
python3 scripts/phase2_gpio_diff.py \
  --xlsx <file.xlsx> --base-col <BASE列> --new-col <NEW列> --explain

python3 scripts/phase2_gpio_diff.py \
  --json-sheet <export.json> --base-col <BASE列> --new-col <NEW列> --explain
```

样例（可换，非规范）：[testRimo](https://www.feishu.cn/sheets/EMjlsfS42hpLaetPAjMcXAOQnnc) · [TestOslo](https://zepp.feishu.cn/wiki/RrNdw4ahxiCoSmkLPSacorFnnJc) · [TestMeru](https://zepp.feishu.cn/wiki/ZloswKpPTiy3BJkcFxuceUtJnPd)

### GPIO 落码（确认后）

- **落点**：profile 起点 + 同目录总线/极性头（如 `board_config.h`）。只改 pinmux、不查总线开关不算做完。
- **成对脚**（UART TX/RX、I2C SCL/SDA 等）：表上的网名可能是对端命名。落码以仓库已有产品的 mux / 总线使能为准；与表字面相反 → 计划标需拍板，**禁止按字面对调**。
- **overlay**：禁止用 NEW **名字**猜对照产品。仅当 NEW 列与某已有产品 pinmux **逐脚比对**命中率高、且计划写明来源时，才允许整文件覆盖；覆盖后仍须按表差补漏（对照产品缺的脚不得留 NC 当完成）。
- **仅清单**：脚本 `kind=alias`（去括号/EINT 后主体相同）不改码。`kind=functional` 时 Agent 仍须判断是否只是别名，是则计划标仅清单并写明理由，不改码。

### 器件落码（`SKILL配置=是`，确认后）

流程（与具体型号无关）：

1. 用该行 **NEW 型号字符串**在仓库 `configs/<平台>/` 与板级目录搜索谁已经这样配。
2. 命中一种现有写法 → 按该写法改 NEW 的对应文件；计划写明对照来源。
3. 零命中、或多产品互相冲突 → 待定，不编造 Kconfig。
4. 只改 NEW 的 defconfig 里**已经出现过同类开关**的文件；某镜像没有该选项则跳过并在计划注明，禁止往无关镜像插入新选项。
5. BASE 与 NEW 在仓库中是两套可同时打开的独立选项 → 需拍板（只开 NEW / 双开 / 只留 BASE），禁止默认关掉 BASE 对应项。

### 平台差异仅此：落点与格式

落点表只是 **搜索起点**（以仓库实文件为准）。文件改名/拆分时：在 `products/<new>/`（及 profile 注明的邻域）按现有产品写法定位，再适配。

| 平台 | GPIO 常见落点 | 常见格式 | 器件 / defconfig |
| --- | --- | --- | --- |
| mhs003 | `products/<new>/board_pinmux_private.c`、`include/board_pinmux.h`、`board_config.h` | 脚名多为 PAxx | `configs/mhs003/*_<new>_*`；型号按上节搜仓库，见 [mhs003.md](profiles/mhs003.md) |
| mhs003s | 同上结构，目录换 `mhs003s` | 同 mhs003 | `configs/mhs003s/*_<new>_*` |
| apollo5 | `products/<new>/board_pin_product.c`、`include/board_pin_product.h` | Pad/GPIO → `AM_HAL_PIN_*` 等 | `configs/apollo5/*_<new>_*`（主名常为 `apollo330_*`）；见 [apollo5.md](profiles/apollo5.md) |

---

## Phase 3 — Bringup 报告导出

**目标**：Phase1/2 完成后，按模板生成飞书 Bringup 报告（【自动】填满，【人工】留空）。

| 资源 | 说明 |
| --- | --- |
| 飞书母版（复制后再填） | [驱动组xx项目Bringup报告(Agent使用)](https://zepp.feishu.cn/wiki/I3Xiw9bbli9nc6kypcbcgpvInJe) |
| 本地同源模板 | [templates/phase3_bringup_report.xml](templates/phase3_bringup_report.xml) |
| 手工填写参考（结构来源） | [Windermere Bringup 例](https://zepp.feishu.cn/wiki/PFL1wqzQjiWR7mkATqhcsyf2nof) |

### 规则（强制）

| 条件 | 行为 |
| --- | --- |
| Phase1 产物不齐，或 Phase2 尚未出过计划 | **停**；或仅导出已完成范围并在报告注明 |
| 【自动】字段 | 来自仓库 / Phase2 表 / 已确认计划；**禁止编造**链接与「已完成」 |
| 【人工】字段 | 原理图、软件计划、硬件环境、日报、§3.1 CI、§3.2 备注与远程分支确认、§3.3、§4 影响功能/责任人/确认、§6 勾选 →「待人工」或留空；**勿**把 §3.2 浅黄的 xml/defconfig 文件名当成人工项；**勿**把 §4 影响固件当成人工项 |
| 占位符 `{{…}}` | 导出完成后文档中 **不得残留** |
| callout | 固定两段：标题「Skill Phase3 导出」+ 填色说明。禁止加「实战副本 / 母版」等；禁止把占位符清单渲到报告 |
| 报告正文 | 禁止本机绝对路径；模板里给 Agent 的填表提示不得原样写进项目单元格 |
| 飞书写入 | Windows `cmd.exe` + `lark-cli`（用户身份）；**复制母版 → 对副本写入**，勿直接当项目报告改母版 |
| 副本路径 | 与 **Phase2 传入的硬件配置表**（`{{HW_DOC}}`）同知识空间、同父节点（表在空间根则副本也在该空间根）。**禁止**落到母版所在目录 |
| §4 **影响固件** | 自动填，只允许 `jlinkbin` / `boot` / `recovery` / `watch` / `FCT` / `HT`。对照 §3.2 对应 NEW defconfig，该行适配实际改过/打开的选项出现在哪些镜像就列哪些；没有该选项则不写。禁止追加 ifx55532 等表头以外的镜像名，禁止填「全部」或把「待填（如watch/boot/…）」留在浅黄格 |

### 步骤

1. 定位副本路径（强制：跟硬件表，不跟母版）：
   - `wiki +node-get` **传入的硬件配置表** → 取其 `space_id`、`parent_node_token`。
   - `wiki +node-copy` 母版到该位置：`--target-space-id` = 硬件表的 `space_id`；硬件表 `parent_node_token` 非空则再加 `--target-parent-node-token`（与表同级），为空则只指定 `--target-space-id`（空间根）。
   - 标题 `驱动组<NEW>项目Bringup报告`。失败则停。
   - **禁止**用母版自己的 `space_id` / `parent_node_token` 当复制目标。禁止改母版。
2. 汇总 Phase1 校验、defconfig 对照、板型宏；Phase2 `{{HW_DOC}}` 链接、GPIO 差异、风险；§4 器件落地按需展开。
3. 用 `scripts/phase3_fill.py`（或等价全局替换）填 `templates/phase3_bringup_report.xml`：**所有** `{{…}}` 都要换掉；§2 器件明细不抄表（只填硬件配置表链接）；§4/GPIO 按实际行数展开。callout 不得改写。`{{REPO}}` 只填仓库根目录名。GPIO 仅清单行代码文件填「—」。风险一项一条。影响固件见上规则。导出前检查不得残留 `{{…}}`。
4. 对**副本** `docs +update --command overwrite`；写后 `+fetch` 再确认无占位符。
5. 交还用户副本链接，并列出待补【人工】项。

### 章节对应（与原 Bringup 报告同序）

| 报告节 | 内容 | 填充 |
| --- | --- | --- |
| §1 表格建立时间点 | 填表时间、PL | 【人工】+ 导出日期自动 |
| §2 硬件变更确认 | 参考项目、原理图、PDCP 差异、Phase2 硬件配置表链接、GPIO 链接、硬件环境、计划 | 自动 + 人工（【必须有】对齐原模板；器件明细以链接为准，不重复抄表） |
| §3 Codebase | 3.1 环境/CI；3.2 分支配置表；3.3 .config 差异；3.4 宏 | 3.2（含 xml 文件名/字串）与 3.4 自动；3.1 CI 与远程分支、3.3 人工 |
| §4 硬件变更和确认 | 器件落地表（含影响/责任人）、GPIO 差异、风险 | 型号/动作/影响固件/GPIO【自动】；影响功能与确认【人工】 |
| §5 日报 | 过程日报 | 【人工】 |
| §6 检查 | 勾选确认 | 【人工】 |

**禁止**：未写入真实副本时声称 Phase3 已完成；伪造飞书链接。
