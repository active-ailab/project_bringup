# 命令

## Phase 1（新建工程骨架）

在 Skill 目录下。飞书硬件模板 **不能**替代本步。

```bash
# apollo5：meru → testmeru（或 fuji → testfuji）
python3 scripts/phase1_clone_product.py \
  --repo-root <HMOS_ROOT> --platform apollo5 \
  --base meru --new testmeru --dry-run

# mhs003：rimo → testrimo
python3 scripts/phase1_clone_product.py \
  --repo-root <HMOS_ROOT> --platform mhs003 \
  --base rimo --new testrimo --dry-run

# mhs003s：oslo → testoslo
python3 scripts/phase1_clone_product.py \
  --repo-root <HMOS_ROOT> --platform mhs003s \
  --base oslo --new testoslo --dry-run
```

确认清单后去掉 `--dry-run`。`--new` 用硬件表原文（勿自行改大小写）。校验：仓库里已有 `products/<new>`、主 defconfig、`Config.in` 板型符号（表勾选不能替代）。

## Phase 2（器件 / GPIO）

三平台（apollo5 / mhs003 / mhs003s）**同一流程**；差异只在 profile 里的代码路径与格式。Skill **不**维护器件型号名单。

**顺序强制**：读飞书 → 比差异 → 整理变更计划 → **用户确认** → 按仓库实文件适配。未确认禁止写仓库。

1. 以仓库确认 Phase1 产物（表勾「已完成」不够）。
2. 用户投喂：[硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（黄格必填：身份/GPIO/器件类型与型号/SKILL配置；供别与备注可选）。
3. Agent 只分析：校验必填 → GPIO 动态出差异并分类 → 器件逐行按仓库现写法分类 → 输出变更计划（需拍板单列）。
4. 用户确认范围：`确认全部` / `确认全部，<拍板结论>` / 部分 / `取消`。
5. 确认后再改代码；改完做校验。

GPIO 链接先判定类型再取数：

```bash
lark-cli drive +inspect --url <§2链接>
# 电子表格：lark-cli drive +export --file-extension xlsx --output-dir ... --overwrite
# 文档：   lark-cli docs +fetch --doc <链接>
```

GPIO 差异（计划阶段用；必须 `--explain`，多 sheet 时加 `--sheet`）：

```bash
python3 scripts/phase2_gpio_diff.py \
  --xlsx <你的表.xlsx> --base-col <BASE列> --new-col <NEW列> --explain

python3 scripts/phase2_gpio_diff.py \
  --xlsx <你的表.xlsx> --sheet <工作表名> --base-col <BASE列> --new-col <NEW列> --explain

python3 scripts/phase2_gpio_diff.py \
  --json-sheet <export.json> --base-col <BASE列> --new-col <NEW列> --explain
```

历史示例表（可换，非规范）：

- [testRimo](https://www.feishu.cn/sheets/EMjlsfS42hpLaetPAjMcXAOQnnc)
- [TestOslo xlsx](https://zepp.feishu.cn/wiki/RrNdw4ahxiCoSmkLPSacorFnnJc)
- [TestMeru xlsx](https://zepp.feishu.cn/wiki/ZloswKpPTiy3BJkcFxuceUtJnPd)

## Phase 3（Bringup 报告）

1. 复制母版到 **硬件配置表同路径**（不要放到母版目录）：
   - 母版：[Bringup报告(Agent使用)](https://zepp.feishu.cn/wiki/I3Xiw9bbli9nc6kypcbcgpvInJe)
   - `wiki +node-get` **传入的硬件配置表**，取其 `space_id` / `parent_node_token`
   - 再 copy（`--target-*` 全部来自硬件表，不是母版）：

```bash
# 硬件表在某父节点下：与表同级
lark-cli wiki +node-copy --node-token I3Xiw9bbli9nc6kypcbcgpvInJe \
  --target-space-id <HW_SPACE_ID> \
  --target-parent-node-token <HW_PARENT_NODE_TOKEN> \
  --title 驱动组<NEW>项目Bringup报告 --yes

# 硬件表在知识空间根（parent 为空）：只指定目标空间
lark-cli wiki +node-copy --node-token I3Xiw9bbli9nc6kypcbcgpvInJe \
  --target-space-id <HW_SPACE_ID> \
  --title 驱动组<NEW>项目Bringup报告 --yes
```

2. 用脚本填【自动】节（全局替换，含 `<code>` 里的占位符）：

```bash
python3 scripts/phase3_fill.py \
  --template templates/phase3_bringup_report.xml \
  --json <replacements.json> --out <filled.xml>
```

   §2 器件明细不抄表，只填硬件配置表链接；§4 仅 BASE≠NEW（需落地）行展开。
3. 对**副本** `lark-cli docs +update --command overwrite`（Windows `cmd`）；勿改母版当项目报告。
4. `+fetch` 确认无残留 `{{…}}`；列出待补【人工】项。

手工结构参考：[Windermere Bringup](https://zepp.feishu.cn/wiki/PFL1wqzQjiWR7mkATqhcsyf2nof)
