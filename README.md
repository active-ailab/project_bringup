# project-bringup

用于 HMOS 新项目导入（Bringup）：基于已有 **BASE** 产品克隆 **NEW**，并完成器件 / GPIO 等硬件适配。

| 步骤 | 做什么 | 用户要做什么 |
|---|---|---|
| Phase1 | 克隆并挂接工程骨架 | **直接提问即可**，不用填表 |
| Phase2 | 按飞书硬件表适配器件 / GPIO | **先填表**，再提问 |
| Phase3 | 导出 Bringup 飞书报告 | 提问即可（Phase1/2 做完后） |

平台：`mhs003` · `mhs003s` · `apollo5`。  
飞书硬件表只用于 Phase2，不能单独新建工程。  
Skill 管流程，不维护器件型号名单；NEW 名以硬件表原文为准。

规范见 [SKILL.md](SKILL.md)。

---

## 怎么用（按顺序）

### 第一步：新建工程（不用填表）

直接说平台、BASE、NEW（不说仓库路径 = 当前工程）：

```text
用 project-bringup Skill，基于 mhs003 平台 rimo，新建 xxx。
```

Agent 会 dry-run → 你确认后真正复制。  
完成后会问：**是否一键上库？** 说「是」才 commit/push；说「否」则本地保留改动。

### 第二步：硬件适配（要填表）

1. 复制 [硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)，按黄格填好（平台 / BASE / NEW、GPIO、器件等）。
2. 再提问，把**你的副本链接**丢给 Agent：

```text
用 project-bringup Skill，按我填好的硬件表 <副本链接>，适配 xxx。
```

流程：读表 → 出变更计划 → **你确认计划后才改代码** → 校验 → 再问是否上库。  
确认时可说：`确认全部` / `只改器件，GPIO 先不动` / `确认全部，保留 <旧配置…>`。

### 第三步：导出报告

```text
用 project-bringup Skill，导出 xxx 的 Bringup 报告。
```

会复制飞书母版并自动填【自动】项；【人工】项留给你补。

### 连做

```text
用 project-bringup Skill，基于 mhs003 平台 rimo，新建 xxx；
表填好后再按 <副本链接> 做硬件适配；完成后导出 Bringup 报告。
```

中间仍会在「改代码前 / 上库前」停下来等你确认。

---

## 中间会卡你的节点

| 时机 | 你需要 |
|---|---|
| Phase1 dry-run 后 | 确认是否真正执行复制 |
| Phase1 / Phase2 改完后 | 确认是否一键上库（默认不上） |
| Phase2 出计划后 | 确认变更范围（未确认不改仓库） |

---

## 模板

- 硬件表模板：[项目Bringup硬件配置模板](https://zepp.feishu.cn/wiki/OR4Tw7BNRi96gEkmSNUcvzstnMc)
- 报告母版：[Bringup报告(Agent使用)](https://zepp.feishu.cn/wiki/I3Xiw9bbli9nc6kypcbcgpvInJe)
