# apollo5

板型：`HMI_BOARD_APOLLO330P_` + 产品名大写。路径相对 HMOS 根。`module.mk` 不改。

## 复制

| 源 | 目标 |
|---|---|
| `platform/board/apollo5/products/<base>/` | `products/<new>/` |
| `configs/apollo5/` 中产品名成词匹配的文件 | 文件名 base→new |
| `.repo/manifests/` 成词匹配 `*.xml` | 文件名与内容中产品 token / `releases/<base>/` → NEW |
| `components/hal/sensor/include/<base>/`（若有） | `include/<new>/` |

defconfig 定向替换：板型符号、`HMI_PRODUCT_CUSTOMIZE_DIR`、`BX_CHIP_APOLLO330B_BIN_FOLDER`、sku 路径、`ramdump_<base>@`；`PRODUCT_DEVICE_NAME` 仅值等于 base 时改。

sport 分产品头：有则复制并挂 dispatcher；无则跳过（如 fuji）。

## 挂接

| 范围 | 做法 |
|---|---|
| `Config.in` | 新板型 + `default "<new>"` |
| `components/hal/module.mk` | 复制 BASE 的 `ifeq` 传感器 include 块到 NEW |
| board / flash 等含 BASE 板型的 `#if` | `BASE \|\| NEW` |
| BLE 版本记录 | 有 `[base]` 则追加 `[new]` |

## 校验

`products/<new>`、`apollo330_<new>_defconfig`、`Config.in` 含新板型。

## Phase2（流程同 SKILL；此处只写落点/格式）

**前提**：Phase1 已完成。数据输入：[项目Bringup硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)（§1 填 `apollo5`）。**总流程与 mhs003/mhs003s 相同**，见 [SKILL.md](../SKILL.md)。

GPIO 样式示例（可换）：[TestMeru](https://zepp.feishu.cn/wiki/ZloswKpPTiy3BJkcFxuceUtJnPd)。解析：`scripts/phase2_gpio_diff.py --explain`。

| 项 | 起点（以仓库实文件为准） |
|---|---|
| GPIO | `platform/board/apollo5/products/<new>/board_pin_product.c`、`include/board_pin_product.h` |
| 其它板级 | `bsd_regulator.h`、partition 等（按需） |
| defconfig | `configs/apollo5/*_<new>_*`（主名常为 `apollo330_<new>_defconfig`） |

**GPIO 格式**：常见 Pad/GPIO → `AM_HAL_PIN_*`；以 NEW 产品树现有写法为准适配。成对脚 / overlay / 仅清单规则见 [SKILL.md](../SKILL.md)。  
**器件**：不按型号表映射。`SKILL配置=是` 时按 [SKILL.md](../SKILL.md)「器件落码」在仓库搜索；映射不到则计划标待定，不编造。
