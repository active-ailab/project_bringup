---
name: project-bringup
description: >-
  基于 BASE 产品克隆 HMOS 新项目并做硬件适配。Phase1：全平台克隆挂接。
  Phase2：多平台同一流程（读飞书文档→比差异→计划确认→按仓库实文件适配）；
  表样式与代码落点实时识别，细节见各平台 profile。Phase3 待补。
disable-model-invocation: true
---

# HMOS 项目 Bringup

从 **BASE** 派生 **NEW**。只按本 Skill 执行。


| 步骤      | 内容                     | 状态                                  |
| ------- | ---------------------- | ----------------------------------- |
| Phase 1 | 复制 BASE→NEW 并挂接编译/配置   | **已实现**（apollo5 / mhs003 / mhs003s） |
| Phase 2 | 硬件表适配器件、GPIO           | **同一流程**；平台差异仅在落点与代码格式（见 profile）   |
| Phase 3 | 导入报告 + 生成 bringup 飞书文档 | **TODO**                            |


未实现的能力禁止假装完成（当前仅 Phase3）。

## 原理

产品绑定：

1. **目录** `platform/board/<platform>/products/<name>`，由 `HMI_PRODUCT_CUSTOMIZE_DIR` 选中
2. **板型** `HMI_BOARD_<PREFIX>_<NAME_UPPER>`（`Config.in` choice + default）
3. **defconfig / 条件编译 / 资源名** 打开该板型，并挂接共享代码与资源


| 平台        | 板型前缀                    | 主 defconfig                 | Phase1 | Phase2            |
| --------- | ----------------------- | --------------------------- | ------ | ----------------- |
| `mhs003`  | `HMI_BOARD_MHS003_`     | `mhs003_<new>_defconfig`    | ✅      | ✅ 同流程；落点见 profile |
| `mhs003s` | `HMI_BOARD_MHS003S_`    | `mhs003s_<new>_defconfig`   | ✅      | ✅ 同流程；落点见 profile |
| `apollo5` | `HMI_BOARD_APOLLO330P_` | `apollo330_<new>_defconfig` | ✅      | ✅ 同流程；落点见 profile |


细则：[profiles/apollo5.md](profiles/apollo5.md) · [profiles/mhs003.md](profiles/mhs003.md) · [profiles/mhs003s.md](profiles/mhs003s.md)

通用规则：先 dry-run/列出变更再 apply；默认不 commit；文件清单按 BASE **动态发现**，不写死白名单。Phase1 不改 PNP/广播名/pin 数值。

**关键**：飞书硬件模板 **只服务 Phase2**，不能单独「新建项目」。新建 = Phase1 脚本 → 再填模板做 Phase2。

---



## Phase 1

锁定：`平台`、`仓库根`、`base`、`new`。在本 Skill 目录执行：

```bash
python3 scripts/phase1_clone_product.py \
  --repo-root <HMOS_ROOT> --platform <apollo5|mhs003|mhs003s> \
  --base <base> --new <new> --dry-run
```

确认后去掉 `--dry-run`。命令见 [examples.md](examples.md)。

校验：`products/<new>`、主 defconfig、`Config.in` 含新板型符号。

---



## Phase 2 — 器件 / GPIO



### 总原则（三平台相同）

**mhs003 / mhs003s / apollo5 走同一套流程。** 平台差异只在：


| 变的是什么        | 怎么处理                                                   |
| ------------ | ------------------------------------------------------ |
| GPIO / 器件表样式 | **实时识别**表头、脚标识、产品列（示例表仅供参考）                            |
| 代码路径、宏/脚名格式  | 按 §1 平台查 profile「落点」；**以仓库实文件为准**，路径/文件名变了就按现仓库找，不硬套旧名 |
| 器件型号→配置      | 先查 profile 对照；无对照则对照 BASE/同类产品在仓库中的写法，映射不到则标待定         |


不变的总流程：

**读表 → 比较差异 → 出变更计划 → 用户确认 → 按当前代码格式适配 → 校验**

禁止把「有没有单独写回 .py」当成能力缺口；落码由 Agent 按计划改仓库即可。解析优先用/扩展 `scripts/phase2_gpio_diff.py`，禁止每次从零新写一份解析脚本（除非现脚本无法扩展）。

### 数据输入（飞书，三平台共用）

[项目Bringup硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（rev≥184 结构）  
模板：**黄格=必填**，无黄底=选填。含填写规范与示例；**不含**识别/写回流程。读飞书用 Windows 侧 `cmd.exe` + `lark-cli`。


| 节   | 必读字段（黄格）                                  | 选填（可忽略）   | Agent       |
| --- | ----------------------------------------- | --------- | ----------- |
| §0  | —（规范给人看）                                  | —         | 语义以本节「规则」为准 |
| §1  | 平台 / BASE / NEW / Phase1 状态               | —         | 必读          |
| §2  | GPIO 链接、BASE/NEW 列名、`GPIO·SKILL配置`        | 工作表名      | 必读          |
| §3  | **器件类型**、BASE **型号**、NEW **型号**、`SKILL配置` | 供别、备注（厂家） | 逐行读；厂家不参与映射 |
| §4  | 状态均为「完成」                                  | —         | 任一项未完成 → 停  |




### 规则（强制）


| 条件                               | 行为                                                 |
| -------------------------------- | -------------------------------------------------- |
| §1 Phase1≠已完成，或 §4 有「未完成」        | **禁止**做 Phase2 写回；先 Phase1 / 补表                    |
| §1/§2/§3 必填黄格缺失或型号空泛（如只写「电源芯片」）  | **停**，请用户补齐后再出计划                                   |
| **未获用户确认变更清单**                   | **禁止改仓库任何文件**；只允许读表、分析、输出计划                        |
| 同一器件多行（一供/二供等）                   | **逐行**比较型号与 `SKILL配置`，分别写入计划                       |
| 器件 BASE 型号 = NEW 型号（或 NEW 为「同左」） | **禁止改**该器件；按仅检查                                    |
| NEW 为「无」/「（无…）」等且 BASE 有型号       | 视为型号变更（相对 BASE 去掉或换方案），按 `SKILL配置` 处理              |
| 器件 `SKILL配置` 空                   | BASE=NEW（或同左）→ 仅检查；BASE≠NEW → 按否                   |
| 器件 `SKILL配置=否`                   | **禁止自动适配**；计划里记「仅报告」                               |
| 器件 `SKILL配置=是`                   | 按 **该行 NEW 型号** 查 profile / 仓库同类写法；无映射则标待定，确认后仍不瞎改 |
| `GPIO·SKILL配置=否`                 | 计划只含差异清单，确认后仍不改代码                                  |
| `GPIO·SKILL配置=是`                 | 计划含拟改文件/脚；用户确认后再按仓库实格式写回                           |
| 备注/厂家                            | 可展示，**不参与**映射判断                                    |
| 始终                               | 不改板型符号、`HMI_PRODUCT_CUSTOMIZE_DIR`、BASE 产品树        |




### 步骤（强制：计划 → 确认 → 再改码）

投喂 [硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（或同结构副本）后：

1. **读 §1 / §4**：平台、base、new、Phase1、确认状态；校验必填黄格齐全；仓库确认 `products/<new>` + 主 defconfig + `Config.in` 板型存在。
2. **分析 §2 GPIO + §3 器件**（只读不写）：GPIO 动态出差异；器件 **逐行**（含一供/二供）按规则分类。在仓库中定位当前落点与代码格式（见下表与 profile）。整理成 **变更计划**。
3. **停下来请用户确认**：展示计划；问清「全部按计划改 / 只改某几项 / 先不改」。**未明确同意前禁止改代码。**
4. **用户确认后**再执行适配（仅确认范围内的项）；映射不到的项保持待定并说明。
5. **校验**：实际改动与确认范围一致；板型/CUSTOMIZE_DIR 未误改。



### 计划输出格式（确认前必须给出）

用简洁列表，至少包含：


| 类别      | 每条写清                                                  |
| ------- | ----------------------------------------------------- |
| 器件      | 类型、供别（若有）、BASE→NEW **型号**、`SKILL配置`、拟动作；备注/厂家可附带但不作依据 |
| GPIO    | 脚标识、BASE信号→NEW信号、拟改文件（或「仅清单」）、不确定项                    |
| 风险 / 不做 | 必填缺失、无映射、需用户拍板的点                                      |


用户可回复例如：`确认全部` / `只改器件，GPIO 先不动` / `取消`。

### GPIO：固定流程 + 动态识别（强制）

两段式（缺一段都不算 Phase2 GPIO 做完）；落码必须在用户确认计划之后：

1. **解析**：动态认表 → 对齐 BASE/NEW 列 → 出差异清单（与平台无关）→ **写入变更计划**。
2. **落码**（仅确认后）：在 `platform/board/<平台>/products/<new>/` 等处 **实时找到** GPIO 定义文件与现有写法，按差异改；找不到或对不上格式 → 标待定，不编造。

模板/文档里的表示例 **只是样例**，不绑定某平台只能用某例。Agent **禁止**按「必须是例1/2/3」硬套。


| 步   | 做什么           | 要点                                                                              |
| --- | ------------- | ------------------------------------------------------------------------------- |
| 1   | 取用户 §2 链接     | 在线表或 xlsx；不要求长得像示例                                                              |
| 2   | 定位「产品矩阵」表     | 多 sheet 时找同时含 BASE/NEW 产品列的页（可 `--sheet`，否则脚本自动选）                               |
| 3   | 发现表头行         | 含产品列名的那一行（不假设第 0 行）                                                             |
| 4   | 发现脚标识列        | 动态认 `PIN Name` / `Pin` / `Pad` / `GPIO` / `Net` / 「脚名」等；可多列；跳过 Function/描述/Type |
| 5   | 对齐 BASE/NEW 列 | 用 §2 列名模糊匹配；对不上就停并列出实际表头，禁止猜                                                    |
| 6   | 逐行 diff       | 只保留 BASE信号 ≠ NEW信号；空与 `NC` 标明未使用                                                |
| 7   | 纳入变更计划        | 拟改文件与脚；`GPIO·SKILL配置=否` 则计划标注「不改码」                                              |
| 8   | 用户确认后落码       | 仅已确认项；按平台 profile 起点在仓库中定位并适配格式                                                 |


```bash
python3 scripts/phase2_gpio_diff.py \
  --xlsx <file.xlsx> --base-col <BASE列> --new-col <NEW列> --explain

python3 scripts/phase2_gpio_diff.py \
  --json-sheet <export.json> --base-col <BASE列> --new-col <NEW列> --explain
```

样例（可换）：[testRimo](https://www.feishu.cn/sheets/EMjlsfS42hpLaetPAjMcXAOQnnc) · [TestOslo](https://zepp.feishu.cn/wiki/RrNdw4ahxiCoSmkLPSacorFnnJc) · [TestMeru](https://zepp.feishu.cn/wiki/ZloswKpPTiy3BJkcFxuceUtJnPd)

### 平台差异仅此：落点与格式（起点；以仓库实文件为准）


| 平台      | GPIO 常见落点                                                          | 常见格式                        | 器件 / defconfig                                                                                   |
| ------- | ------------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------ |
| mhs003  | `products/<new>/board_pinmux_private.c`、`include/board_pinmux.h`   | 脚名多为 PAxx                   | `configs/mhs003/*_<new>_*`；型号对照见 [mhs003.md](profiles/mhs003.md)                                 |
| mhs003s | 同上结构，目录换 `mhs003s`                                                 | 同 mhs003                    | `configs/mhs003s/*_<new>_*`；型号对照复用 mhs003                                                        |
| apollo5 | `products/<new>/board_pin_product.c`、`include/board_pin_product.h` | Pad/GPIO → `AM_HAL_PIN_*` 等 | `configs/apollo5/*_<new>_*`（主名常为 `apollo330_*`）；对照见 [apollo5.md](profiles/apollo5.md)，无则对照仓库同类产品 |


落点表只是 **搜索起点**。文件改名/拆分时：在 `products/<new>/`（及 profile 注明的邻域）按现有产品写法定位，再适配。

---



## Phase 3 — TODO

**目标**：适配完成后输出导入报告，并按模板生成 bringup 文档。

- Bringup 模板：[wiki](https://zepp.feishu.cn/wiki/wikcnknOLR76YvkwqrJCiKCcSxb?from=navigation)

**待补回**：

- [ ] 汇总 Phase1/2 变更与风险
- [ ] 生成导入/适配报告
- [ ] 按模板写飞书 bringup 文档（`lark-cli`，Windows `cmd` + 用户身份）
- [ ] 需要时加 `scripts/phase3_*.py`

**禁止**：未完成时声称 Phase3 已完成或伪造飞书链接。