# mhs003s

板型：`HMI_BOARD_MHS003S_` + 产品名大写。路径相对 HMOS 根。`module.mk` 不改。

前提：`products/<base>` 与 `Config.in` 中 BASE 板型均存在（仅有 defconfig 不够）。

## 复制

| 源 | 目标 |
|---|---|
| `platform/board/mhs003s/products/<base>/` | `products/<new>/`（含 sensorhub） |
| `configs/mhs003s/` 成词匹配文件 | 文件名 base→new |
| `.repo/manifests/` 成词匹配 `*.xml` | 文件名与内容中产品 token / `releases/<base>/` → NEW |
| sport 分产品头（有则拷） | `*_<new>.h` |
| `<base>_sensor_config.json` / `gnss_<base>_config.json`（有则拷） | `<new>_…` |
| `ramdump/**/<base>/` | `…/<new>/`（文件名产品 token 同步改） |
| `ui/**/config.json` 的 `projects.<base>` | 增加 `projects.<new>` |

defconfig 定向替换：板型、`HMI_PRODUCT_CUSTOMIZE_DIR`、`BX_CHIP_RTL8763EFL_BIN_FOLDER`、`mhs003s_<base>_sku`、`BUILD_PROJECT_PATH_NAME`（值=base 时）、`ramdump_<base>@`。

## 挂接

| 范围 | 做法 |
|---|---|
| `Config.in` | 新板型 + default |
| sport dispatcher / `sport_rt_attr_auto.c` | `#elif (NEW)` → 新头文件 |
| hal / gnss `module.mk` | 复制 BASE `ifeq` 块到 NEW |
| NFC / logo / applist / UI 相关含 BASE 板型处 | `BASE \|\| NEW` |

## 校验

`products/<new>`、`mhs003s_<new>_defconfig`、`Config.in` 含新板型。

## Phase2（流程同 SKILL；此处只写落点/格式）

**前提**：Phase1 已完成。数据输入：[项目Bringup硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（§1 填 `mhs003s`）。**总流程与 mhs003/apollo5 相同**，见 [SKILL.md](../SKILL.md)。

GPIO 样式示例（可换）：[TestOslo](https://zepp.feishu.cn/wiki/RrNdw4ahxiCoSmkLPSacorFnnJc)。解析：`scripts/phase2_gpio_diff.py --explain`。

| 项 | 起点（以仓库实文件为准） |
|---|---|
| GPIO | `platform/board/mhs003s/products/<new>/board_pinmux_private.c`、`include/board_pinmux.h`、`include/board_config.h`（格式同 mhs003，多为 PAxx） |
| 器件 / defconfig | `configs/mhs003s/*_<new>_*`；器件落码流程见 [SKILL.md](../SKILL.md)，路径换本平台 |
