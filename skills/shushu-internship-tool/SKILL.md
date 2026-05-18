---
name: shushu-internship-tool
description: "Use when an AI assistant helps the maintainer turn a desensitized internship project description into a ready-to-publish aijobfit blog post (.tsx)."
---

# shushu · aijobfit 应届分支内容工厂

默认输出中文，保留英文技术术语。

## 这个 skill 不是什么

- 不是通用简历生成器
- 不是多步可选工作流
- 不是 STAR / 面经 / RAG / 知识库工具

## 这个 skill 是什么

把一份脱敏后的实习项目描述喂给 `shushu.generate_case`，得到一份能直接放进 `aijobfit/src/components/blog/posts/` 的 React 组件文件。

## 唯一命令

```bash
python -m shushu.generate_case \
  --input path/to/project.md \
  --target-role <role_id> \
  --out out/
```

`<role_id>` 必须是 aijobfit 14 角色之一，见 `shushu/data/aijobfit_roles.json`。

## 协助用户的步骤

1. 确认用户已经把项目原始描述脱敏（不含真实公司名、产品名、未公开指标、用户数据、密钥）。
2. 帮用户确定 `--target-role`：把项目核心动作 / 技术栈对照 `aijobfit_roles.json` 的 `required_skills` 找最贴的角色 id。如果两个都贴，建议跑两次。
3. 跑命令，拿到 `.tsx` + `raw/*.md`。
4. 让用户人工审阅 `raw/*.md`（抽取/扫描/改写/追问 四段 JSON），把 `[待补：...]` 的真实数字补上后再发 PR 到 aijobfit。

## 输出约束（来自 prompt 模板）

- 不编造数字
- 不出现：赋能 / 全链路 / 闭环 / 降本增效 / 打通 / 大幅 / 显著 等词
- 简历 bullet：动词 + 量化或 `[待补：...]` + 业务上下文
- 面试追问只给答法骨架，不替候选人编内容

## 角色数据同步

aijobfit 更新 `public/data/roles-domestic.json` 后，需要手动重生成 `shushu/data/aijobfit_roles.json` 并在 commit message 写明来源 commit hash。
