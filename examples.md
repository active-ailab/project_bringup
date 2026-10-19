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

确认清单后去掉 `--dry-run`。校验：`products/<new>`、主 defconfig、`Config.in` 板型符号。

## Phase 2（器件 / GPIO）

三平台（apollo5 / mhs003 / mhs003s）**同一流程**；差异只在 profile 里的代码路径与格式。

**顺序强制**：读飞书 → 比差异 → 整理变更计划 → **用户确认** → 按仓库实文件适配。未确认禁止写仓库。

1. 确认 Phase1 产物已在仓库。
2. 用户投喂：[硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（黄格必填：身份/GPIO/器件类型与型号/SKILL配置；供别与备注可选）。
3. Agent 只分析：校验必填 → GPIO 动态出差异 → 器件逐行分类 → 在仓库定位落点/格式 → 输出变更计划。
4. 用户确认范围（全部 / 部分 / 取消）。
5. 确认后再改代码；改完做校验。

GPIO 差异（计划阶段用）：

```bash
python3 scripts/phase2_gpio_diff.py \
  --xlsx <你的表.xlsx> --base-col <BASE列> --new-col <NEW列> --explain

python3 scripts/phase2_gpio_diff.py \
  --json-sheet <export.json> --base-col <BASE列> --new-col <NEW列> --explain
```

历史示例表（可换，非规范）：

- [testRimo](https://www.feishu.cn/sheets/EMjlsfS42hpLaetPAjMcXAOQnnc)
- [TestOslo xlsx](https://zepp.feishu.cn/wiki/RrNdw4ahxiCoSmkLPSacorFnnJc)
- [TestMeru xlsx](https://zepp.feishu.cn/wiki/ZloswKpPTiy3BJkcFxuceUtJnPd)
