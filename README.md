# project-bringup

用于 HMOS 新项目导入（Bringup）：基于已有 **BASE** 产品克隆 **NEW**，并完成器件 / GPIO 等硬件适配。

| 步骤 | 做什么 |
|---|---|
| Phase1 | 克隆并挂接工程骨架（脚本） |
| Phase2 | 按飞书硬件表适配器件 / GPIO |
| Phase3 | 导出 Bringup 飞书报告 |

平台：`mhs003` · `mhs003s` · `apollo5`。  
飞书硬件表只用于 Phase2，不能单独新建工程。  
Skill 管流程，不维护器件型号名单；NEW 名以硬件表原文为准。

规范见 [SKILL.md](SKILL.md)。

---

## 怎么提问

先引用本 Skill，再说清：平台、BASE、NEW、仓库路径（不说即为当前工程路径）。

**步骤1 — 新建**

```text
用 project-bringup Skill，基于 mhs003 平台 rimo，新建 xxx。
```

**步骤2 — 硬件适配**

```text
用 project-bringup Skill，按我填好的硬件表 <副本链接，模板https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc>，适配 xxx。
```

**步骤3 — 导出报告**

```text
用 project-bringup Skill，导出 xxx 的 Bringup 报告。
```

**连做**

```text
用 project-bringup Skill，基于 mhs003 平台 rimo，新建 xxx；
表填好后再按 <副本链接> 做硬件适配；完成后导出 Bringup 报告。
```

---

## 示例

| 平台 | BASE → NEW |
|---|---|
| mhs003 | rimo → testrimo |
| mhs003s | oslo → testoslo |
| apollo5 | meru → testmeru |

- 硬件表模板：[项目Bringup硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)
- 报告母版：[Bringup报告(Agent使用)](https://zepp.feishu.cn/wiki/I3Xiw9bbli9nc6kypcbcgpvInJe)
