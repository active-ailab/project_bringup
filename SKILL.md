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

通用规则：先 dry-run/列出变更再 apply；**默认不 commit/push**（Phase1/2 仅在用户确认「上库」后才提交）；文件清单按 BASE **动态发现**，不写死白名单。Phase1 不改 PNP/广播名/pin 数值。

**Skill 管范围和流程，不维护、不限定器件型号。** 任何型号→配置都按该行 NEW 型号在**当前仓库**搜已有写法；profile 只给路径/格式起点，禁止把 profile 或历史项目当成器件白名单。

**关键**：飞书硬件模板 **只服务 Phase2**，不能单独「新建项目」。新建 = Phase1 脚本 → 再填模板做 Phase2。

---

## Phase 1

锁定：`平台`、`仓库根`、`base`、`new`。`--new` = 硬件表 §1 NEW **原文**（大小写、连字符均保留）。禁止为「符合小写惯例」而改拼写。板型宏 = 上表**板型前缀** + NEW.upper()（例 mhs003s→`HMI_BOARD_MHS003S_STOCKHOLM`；apollo5→`HMI_BOARD_APOLLO330P_<NEW>`，**不是** `HMI_BOARD_APOLLO5_`）。

在本 Skill 目录执行：

```bash
python3 scripts/phase1_clone_product.py \
  --repo-root <HMOS_ROOT> --platform <apollo5|mhs003|mhs003s> \
  --base <base> --new <new> --dry-run
```

确认后去掉 `--dry-run`。命令见 [examples.md](examples.md)。

校验（**以仓库为准**，表上「Phase1 已完成」不能替代）：`products/<new>`、主 defconfig、`Config.in` 含新板型符号；有 `.repo/manifests` 时同步复制产品 xml（文件名/内容可自动；远程 git 分支仍须 CI/架构师创建）。

### Phase1 完成后：询问是否一键上库（强制）

校验通过后**必须停下来**，用固定话术询问（把 `<NEW>` 换成实名）：

> 新项目 `<NEW>` 已创建完成，是否要一键将代码上库？

| 用户回复 | 行为 |
| --- | --- |
| `是` / `上库` / `确认上库` / `一键上库` 等肯定 | 按下列格式对 **Phase1 改动过的 git 仓** commit + 推 Gerrit |
| `否` / `不上` / `取消` / 未明确同意 | **禁止** commit/push；进入 Phase2 或结束本轮 |

**上库格式（与历史 topic 一致，例 [stockholm](https://gerrit.huami.com/q/topic:%22stockholm%22)）**

| 项 | 规则 |
| --- | --- |
| Gerrit topic | **NEW 原文**（如 `stockholm`） |
| 提交说明（每个仓一条） | `build \|> [<NEW>] 基于<BASE> 复制项目<短名>仓库代码` |
| `<短名>` | `configs`→`configs`；`platform/board/<platform>`→**`board`**；其余取 Gerrit project 路径**最后一段**（如 `applist`、`hal`、`drivers`、`gnssAdapter`） |
| 范围 | 仅 Phase1 产生的改动；**按路径 stage**，禁止 `git add -A` 夹带无关本地修改；无改动的仓不上 |
| 推送 | 各仓 `git push`/`repo upload` 到对应远程 **for review**，并带上同一 topic |
| 完成后 | 回报 topic 链接：`https://gerrit.huami.com/q/topic:%22<NEW>%22`，并列出各仓 change |

示例（NEW=`stockholm`，BASE=`munich`，configs 仓）：

```text
build |> [stockholm] 基于munich 复制项目configs仓库代码
```

```bash
# 在有改动的仓内（示意；只 add Phase1 相关路径；分支以实际跟踪分支为准）
git add <Phase1相关路径…>
git commit -m "$(cat <<'EOF'
build |> [stockholm] 基于munich 复制项目configs仓库代码

EOF
)"
git push origin HEAD:refs/for/<跟踪分支>%topic=stockholm
```

---

## Phase 2 — 器件 / GPIO

三平台走同一套流程。平台差异只在表样式、代码路径和宏/脚名格式（见下表）。

不变的总流程：

**读表 → 比较差异 → 出变更计划 → 用户确认 → 按当前代码格式适配 → 校验 → 询问上库（确认后才 commit/push）**

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
| 同一器件多行（一供/二供等） | **以 NEW 为准**：NEW 有几供就适配几供；BASE 有而 NEW 无该供 → 关对应配置；**逐行**写入计划，禁止合并 |
| 器件 BASE 型号 = NEW 型号（或 NEW 为「同左」） | **禁止改**该器件；按仅检查（仍须在计划中**单独成行**列出） |
| NEW 为「无」/「（无…）」等且 BASE 有型号 | 视为去掉该型号/该供；`SKILL配置=是` 时关 BASE 对应配置 |
| 器件 `SKILL配置` 空 | BASE=NEW（或同左）→ 仅检查；BASE≠NEW → 按否 |
| 器件 `SKILL配置=否` | **禁止自动适配**；计划里记「仅报告」（仍须单独成行） |
| 器件 `SKILL配置=是` | **按该行 NEW 型号适配**：开 NEW 对应配置；同功能位上 BASE 有、NEW 未列出的旧型号/旧供 → **默认关闭**。用 NEW 型号在仓库搜已有写法（见下「器件落码」）；无映射或冲突 → 待定，确认后仍不瞎改 |
| 仓库里 BASE 与 NEW 对应彼此独立的配置项（可同时为 y） | **禁止**再问「只开 / 双开 / 只留 BASE」。默认只保留 NEW 表中的型号与供别；旧项要保留须用户在确认时**额外说明** |
| `GPIO·SKILL配置=否` | 计划只含差异清单，确认后仍不改码 |
| `GPIO·SKILL配置=是` | 计划含拟改文件/脚；用户确认后再按仓库实格式写回 |
| 备注/厂家 | 可展示，**不参与**映射判断 |
| 始终 | 不改板型符号、`HMI_PRODUCT_CUSTOMIZE_DIR`、BASE 产品树 |
| 计划展示 | **禁止**把多个器件/型号缩成一团（如「NOR二供/EMMC/…」或「CPU/NOR/… 同或同系列」）让用户模糊确认；必须从 §3 **真实文档逐行**加载：器件类型、供别、BASE 型号、NEW 型号、`SKILL配置`、拟动作，**一行一项** |

### 步骤（强制：计划 → 确认 → 再改码）

投喂 [硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（或同结构副本）后：

1. **读 §1 / §4**：平台、base、new、Phase1、确认状态；校验必填黄格齐全。**仓库**确认 `products/<NEW>` + 主 defconfig + `Config.in` 板型存在（表勾选不能替代）。
2. **分析 §2 GPIO + §3 器件**（只读不写）：GPIO 动态出差异并分类；器件从飞书 §3 **逐行加载全部行**（含一供/二供、仅检查、否），按规则分类。在仓库中定位当前落点与代码格式（见下表与 profile）。整理成 **变更计划**（器件一行一项，禁止合并缩写）。
3. **停下来请用户确认**：按「计划输出格式」完整展示；问清范围。**未明确同意前禁止改代码。** 确认话术末尾**必须原样附上**一句：`要保留的旧器件配置需要额外说明`
4. **用户确认后**再执行适配（仅确认范围内的项；用户额外说明要保留的旧配置除外，其余按 NEW 关旧开新）；映射不到的项保持待定并说明。
5. **校验**：实际改动与确认范围一致；板型/CUSTOMIZE_DIR 未误改。
6. **询问是否一键上库**（强制，见下节）；未确认禁止 commit/push。

用户可回复例如：`确认全部` / `确认全部，保留 <旧型号/旧配置…>` / `只改器件，GPIO 先不动` / `取消`。未额外说明保留的旧器件配置，按 NEW 表关闭或不再打开。

### Phase2 落码完成后：询问是否一键上库（强制）

步骤 5 校验通过后：

- **若没有任何 Phase2 文件改动**（全是仅检查/仅报告/待定未改码）：说明「无需上库」，**不要**再问上库；可继续 Phase3。
- **若有改动**：**必须停下来**询问（把 `<NEW>` 换成实名）：

> 项目 `<NEW>` 硬件适配代码已完成，是否要一键将代码上库？

| 用户回复 | 行为 |
| --- | --- |
| `是` / `上库` / `确认上库` / `一键上库` 等肯定 | 按下列格式对 **Phase2 改动过的 git 仓** commit + 推 Gerrit |
| `否` / `不上` / `取消` / 未明确同意 | **禁止** commit/push；可继续 Phase3 或结束本轮 |

**上库格式**

| 项 | 规则 |
| --- | --- |
| Gerrit topic | **NEW 原文**（如 `stockholm`；可与 Phase1 同 topic） |
| 提交说明（每个仓一条） | `build \|> [<NEW>] 适配<短名>仓库硬件` |
| `<短名>` | 同 Phase1：`configs`→`configs`；`platform/board/<platform>`→**`board`**；其余取 Gerrit project 路径**最后一段** |
| 范围 | 仅 Phase2 硬件适配改动；**按路径 stage**，禁止夹带无关本地修改；无改动的仓不上 |
| 同仓再次上库 | Phase1 已推过、Phase2 又改同一仓 → **新 commit** 再 push（新 change 或新 patchset）；勿把 Phase1/2 说明混在同一条 subject |
| 推送 | 各仓推到对应远程 **for review**，同一 topic |
| 完成后 | 回报 `https://gerrit.huami.com/q/topic:%22<NEW>%22`，并列出各仓 change |

示例（NEW=`stockholm`，board 仓）：

```text
build |> [stockholm] 适配board仓库硬件
```

```bash
git add <Phase2相关路径…>
git commit -m "$(cat <<'EOF'
build |> [stockholm] 适配board仓库硬件

EOF
)"
git push origin HEAD:refs/for/<跟踪分支>%topic=stockholm
```

### 计划输出格式（确认前必须给出）

**器件表强制**：与飞书 §3 行一一对应；每行独立展示，禁止把多项缩成「A/B/C…」或「同或同系列」一团。仅检查/否/待定也要逐行列出，用户才能看清确认什么。

| 类别 | 每条写清 |
| --- | --- |
| 器件（逐行） | **器件类型**、**供别**（一供/二供/空）、BASE **型号**、NEW **型号**、`SKILL配置`、拟动作（开/关/仅检查/仅报告/待定 + 仓库对照来源）；备注/厂家可附带但不作依据 |
| GPIO | 脚标识、BASE信号→NEW信号、**功能搬脚 / 仅清单**、拟改文件、不确定项 |
| 技术待确认 | 仅限 GPIO 成对脚与表字面相反、overlay 来源等无法从 NEW 表直接判定的项；**禁止**用「只开/双开」问器件配置 |
| 风险 / 不做 | 必填缺失、无映射、`SKILL配置=否` |

确认区末尾固定提示（强制原文）：

> 要保留的旧器件配置需要额外说明

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
- **成对脚**（UART TX/RX、I2C SCL/SDA 等）：表上的网名可能是对端命名。落码以仓库已有产品的 mux / 总线使能为准；与表字面相反 → 计划标「技术待确认」，**禁止按字面对调**。
- **overlay**：禁止用 NEW **名字**猜对照产品。仅当 NEW 列与某已有产品 pinmux **逐脚比对**命中率高、且计划写明来源时，才允许整文件覆盖；覆盖后仍须按表差补漏（对照产品缺的脚不得留 NC 当完成）。
- **仅清单**：脚本 `kind=alias`（去括号/EINT 后主体相同）不改码。`kind=functional` 时 Agent 仍须判断是否只是别名，是则计划标仅清单并写明理由，不改码。

### 器件落码（`SKILL配置=是`，确认后）

流程（与具体型号无关）：

1. 用该行 **NEW 型号字符串**在仓库 `configs/<平台>/` 与板级目录搜索谁已经这样配（含驱动设备表/JEDEC 等已有写法，不限于 Kconfig 名）。
2. 命中一种现有写法 → 按该写法改 NEW 的对应文件；计划写明对照来源。若命中的是运行时 JEDEC/设备表且无需改 defconfig → 计划标「已有支持，无需改配置」，不算漏适配。
3. 零命中、或多产品互相冲突 → 待定，不编造 Kconfig。
4. 只改 NEW 的 defconfig 里**已经出现过同类开关**的文件；某镜像没有该选项则跳过并在计划注明，禁止往无关镜像插入新选项。
5. **以 NEW 为准关旧开新**：同功能位上，NEW 表列出的型号/供别打开；BASE 有而 NEW 未列出的旧型号/旧供默认关闭。**禁止**再问只开/双开。用户确认时额外说明要保留的旧配置 → 按说明保留。
6. **一供/二供**：按 NEW 行数与供别适配；NEW 无该供而 BASE/当前 defconfig 仍开着 → 关闭。

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
| 【人工】字段 | §1 驱动侧 PL、**代码提交 Topic 链接**；§2 软件项目计划、**项目原理图、硬件配置（硬件提供的原文件）**；日报；§3.1 CI；§3.2 备注与远程分支确认；§3.3；§4 影响功能/责任人/确认；§6 勾选 →「待人工」或留空；**勿**把 §3.2 浅黄的 xml/defconfig 文件名当成人工项；**勿**把 §4 影响固件当成人工项；**勿**在 §2 再抄器件/GPIO 明细表 |
| 占位符 `{{…}}` | 导出完成后文档中 **不得残留** |
| callout | 固定两段：标题「使用 `<cite 项目Bringup SKILL>` 一键适配项目、并导出报告」+ 填色说明。**保留**母版 cite 与该标题原文，禁止改写成「Phase3 导出」等；禁止加「实战副本 / 母版」等；禁止把占位符清单渲到报告 |
| 报告正文 | 禁止本机绝对路径；模板里给 Agent 的填表提示不得原样写进项目单元格 |
| 飞书写入 | Windows `cmd.exe` + `lark-cli`（用户身份）；**复制母版 → 对副本写入**，勿直接当项目报告改母版。拉取母版用 `docs +fetch --detail full`（保留填色） |
| 副本路径 | 与 **Phase2 传入的硬件配置表**（`{{HW_DOC}}`）同知识空间、同父节点（表在空间根则副本也在该空间根）。**禁止**落到母版所在目录 |
| §4 **影响固件** | 自动填，只允许 `jlinkbin` / `boot` / `recovery` / `watch` / `FCT` / `HT`。对照 §3.2 对应 NEW defconfig，该行适配实际改过/打开的选项出现在哪些镜像就列哪些；没有该选项则不写。禁止追加 ifx55532 等表头以外的镜像名，禁止填「全部」或把「待填（如watch/boot/…）」留在浅黄格 |
| §4 适配动作 / GPIO 结果 | 正常自动格浅黄；文案含「待定 / 未改完 / 保留冲突」等 → **深黄**（与母版表头说明一致） |

### 步骤

1. 定位副本路径（强制：跟硬件表，不跟母版）：
   - `wiki +node-get` **传入的硬件配置表** → 取其 `space_id`、`parent_node_token`。
   - `wiki +node-copy` 母版到该位置：`--target-space-id` = 硬件表的 `space_id`；硬件表 `parent_node_token` 非空则再加 `--target-parent-node-token`（与表同级），为空则只指定 `--target-space-id`（空间根）。
   - 标题 `驱动组<NEW>项目Bringup报告`。失败则停。
   - **禁止**用母版自己的 `space_id` / `parent_node_token` 当复制目标。禁止改母版。
2. 汇总 Phase1 校验、defconfig 对照、板型宏；Phase2 `{{HW_DOC}}` 链接、GPIO 差异、风险；§4 器件落地按需展开。
3. 用 `scripts/phase3_fill.py`（或等价全局替换）填 `templates/phase3_bringup_report.xml`：**所有** `{{…}}` 都要换掉；§2 只填参考项目表 + `{{HW_DOC}}` / `{{GPIO_DOC}}` 链接（可带可读文案），**不**再抄器件/GPIO 明细；§2「关键器件变更（Bringup专用）」「GPIO 变更（Bringup专用）」仅填链接；「项目原理图、硬件配置（硬件提供的原文件）」橙格留「待填」【人工】；§3.4 `MACRO_ROWS` / §4/GPIO 按实际行数展开（§3.4 **按仓库**汇总，见上表）。callout **保留**母版 cite 与「一键适配项目、并导出报告」标题，不得改写。GPIO 仅清单行代码文件填「—」。风险一项一条。影响固件与深黄规则见上。导出前检查不得残留 `{{…}}`。
4. 对**副本** `docs +update --command overwrite --doc-format xml --content @<filled.xml>`；写后 `+fetch` 再确认无占位符。勿再传旧版 `--markdown`。
5. 交还用户副本链接，并列出待补【人工】项。

### 章节对应（与母版同序；母版有调整时以飞书母版 + 本地同源模板为准）

| 报告节 | 内容 | 填充 |
| --- | --- | --- |
| §1 表格建立时间点 | 驱动侧 PL；**代码提交 Topic 链接**；Skill 导出日期 | PL / Topic【人工】；`{{DATE}}` 自动。无「填表时间」行 |
| §2 硬件变更确认 | 参考项目（平台/BASE/NEW/一句话）；**关键器件变更（Bringup专用）**=硬件配置表链接；**GPIO 变更（Bringup专用）**=GPIO 表链接；软件项目计划；**项目原理图、硬件配置（硬件提供的原文件）** | 参考项目 + 两链接【自动】；软件计划 / 原理图原文件【人工】 |
| §3 Codebase | 3.1 环境/CI；3.2 分支配置表（无仓库路径行）+ board 前缀说明 + **项目信息核对**；3.3 .config 差异；3.4 板型宏 + **SKILL 挂接摘要**（`{{P1_HOOK_SUMMARY}}`）+ 宏代码表 | 3.2 / 项目信息核对 / 3.4 自动；3.1 CI 与远程分支、3.3 人工。已去掉 `{{REPO}}` / `P1_PRODUCTS_OK` 等独立校验行 |
| §3.2 项目信息核对 | 板级目录；项目宏 | 母版单元格带 Agent 备注：`platform/board/{{PLATFORM}}/products/{{NEW}}(填实际路径)`、`HMI_BOARD_{{PLATFORM}}_{{NEW}}(全大写)`——**只写在 SKILL/填充逻辑里**，**项目报告不得出现这两段括号备注**。板级目录填仓库实路径（通常 `platform/board/<PLATFORM>/products/<NEW>`，以仓库为准）；项目宏填全大写板型宏（前缀见 profiles，apollo5 用 `HMI_BOARD_APOLLO330P_`，禁止 `PLATFORM.upper()` 硬拼）。`phase3_fill.py` 会把母版带备注原文换成实值并剥备注 |
| §3.4 宏代码表（`MACRO_ROWS`） | 代码路径 + 修改说明 | **按 git 仓库分行**（一仓一行，勿一文件一行）。代码路径首行固定写成「`<仓库定位> 仓库：`」（例：`platform/board/mhs003s 仓库：`、`configs 仓库：`），其下再**列出该仓内改动文件**（仓内相对路径，禁止 `*` 通配）。修改说明：合并写该仓改动，但**必须人能看懂**：器件/脚/配置用「从 A 改到 B / 关闭 A / 新增 B」列清（例：`LCD 从 RM690C0/F0 改到 RM6D040`；`MOTOR_EN 从 PC31 改到 PC09`），禁止只写缩写箭头串或「按 NEW 关旧开新」空话 |
| §4 硬件变更和确认 | 器件落地表（含影响/责任人）、GPIO 差异、风险 | 型号/动作/影响固件/GPIO【自动】（待定深黄）；影响功能与确认【人工】 |
| §5 日报 | 过程日报 | 【人工】 |
| §6 检查 | 勾选确认 | 【人工】；勾选文案以母版为准 |

**禁止**：未写入真实副本时声称 Phase3 已完成；伪造飞书链接。
