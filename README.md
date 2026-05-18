# shushu

shushu 不是简历生成器，是给 [aijobfit](https://github.com/LLM-X-Factorer/aijobfit) 应届分支生产示范案例文章的脚本。

输入：一份脱敏后的实习项目原始描述（`.md`）+ 目标角色 id（aijobfit 14 角色之一）。
输出：一篇可直接放进 `aijobfit/src/components/blog/posts/` 的 React 组件文件（`.tsx`）。

> aijobfit 侧的对接说明见 [aijobfit README · 案例文章生产](https://github.com/LLM-X-Factorer/aijobfit#案例文章生产)。

## 工作方式

由 LLM（`claude-sonnet-4-6`，带 prompt caching）驱动 4 步流水线：

1. 抽取：从原始描述拆出「背景 / 我的动作 / 技术细节 / 结果 / 缺失信息」
2. 命中扫描：对照目标角色的 `required_skills / preferred_skills` 找证据
3. 改写：生成「复盘版」（详细，给作者自己看）和「简历压缩版」（≤ 2 bullets）
4. 风险标注：列 3-5 个面试可能追问点 + 标准答法骨架

输出文件名 `${roleId}-${slug}.tsx`，套用 aijobfit `PostShell` 模板（`H2 / P / Ul / DataTable / Callout` 等 helper）。同时把原始抽取/扫描/改写/追问 JSON 写到 `raw/${roleId}-${slug}.md`，方便人工审阅。

## 14 角色数据

`shushu/data/aijobfit_roles.json` 是 [aijobfit `public/data/roles-domestic.json`](https://github.com/LLM-X-Factorer/aijobfit) 的 hard copy（已剔除 `other` 桶）。aijobfit 每次更新角色清单后需要手动同步本文件，并在 commit message 写明来源 commit hash。

## 快速开始

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"

export ANTHROPIC_API_KEY=sk-...

python -m shushu.generate_case \
  --input tests/fixtures/sample_project.md \
  --target-role ai_engineer \
  --out out/
```

输出：

- `out/ai_engineer-sample-project.tsx`
- `out/raw/ai_engineer-sample-project.md`

把 `.tsx` 直接复制进 `aijobfit/src/components/blog/posts/`，再在 `src/data/blog-posts.ts` 注册即可。

## Prompt 约束

- 不编造数字。原始材料里没的指标一律 `[待补：xx 类指标]`
- 不用「赋能 / 全链路 / 闭环 / 降本增效 / 打通 / 大幅 / 显著」一类词
- 简历版每条 bullet 强制：动词 + 量化或 `[待补：...]` + 业务上下文
- 面试追问只给「先答 X、再补 Y、最后落到 Z」骨架，不替候选人编内容

## 开发

```bash
pytest
```

## 安全提醒

`--input` 进的文件请务必先脱敏，不要把公司未公开的内部数据、用户信息、密钥、内部文档原样喂给 LLM。

## License

Apache-2.0，见 [LICENSE](./LICENSE)。
