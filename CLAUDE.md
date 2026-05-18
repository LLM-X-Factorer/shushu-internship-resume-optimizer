# shushu

aijobfit 应届分支示范案例文章的生产脚本。单一入口 `python -m shushu.generate_case --input <md> --target-role <id> --out <dir>`。

## 与 aijobfit 的边界

aijobfit 是产品（Next.js Web App，生产环境 aijobfit.llmxfactor.cloud，求职用户访问）。shushu 是产品旁边的离线小工具（Python 脚本，维护者本地一次性运行，永远不上线）。

**数据所有权**：

- `roles-domestic.json` 的源在 aijobfit（`public/data/`）。shushu 这边的 `shushu/data/aijobfit_roles.json` 是 hard copy，只读，过期就过期。
- aijobfit 更新角色清单 → 手动重新拉一份覆盖到 shushu，commit message 写来源 commit hash。
- 角色定义冲突时 **aijobfit 说了算**。

**输出方向**：

- shushu 写 `out/*.tsx` → 人工审阅 + 补 `[待补：...]` → 复制到 `aijobfit/src/components/blog/posts/` → 在 `aijobfit/src/data/blog-posts.ts` 注册。单向，不回流。
- 生成的 `.tsx` 单篇润色 / 数字补齐：直接在 aijobfit 那份手改，**不要回流到 shushu**。
- prompt / 渲染模板问题：改 shushu 重生成。
- `PostShell` API 变了：先改 aijobfit，再来 shushu 改 `render.py`，否则下一篇会 build 失败。

**shushu 明确不做**（避免边界蔓延）：通用简历生成器 / runtime 服务 / 多角色路由 / RAG / 知识库 / 用户分析 / SEO。这些全归 aijobfit。

## 输出契约（写在 `shushu/prompts.py` 的 SYSTEM_PROMPT 里）

- 不编造数字。原始材料里没有的指标一律 `[待补：xx 类指标]`。
- 禁用词：赋能 / 全链路 / 闭环 / 降本增效 / 打通 / 大幅 / 显著 / 抓手 / 颗粒度 / 对齐 / 底层 / 生态。
- 简历版 bullet 强制结构：动词 + 量化或 `[待补：...]` + 业务上下文。
- 面试追问只给「先答 X、再补 Y、最后落到 Z」骨架，不替候选人编内容。

放宽这些约束属于产品契约变更，要先和 aijobfit 维护者对齐。

## 架构

- `shushu/generate_case.py` — CLI 入口 + 4 步流水线编排
- `shushu/prompts.py` — 4 个 prompt 模板，每个带 `TASK_TAG: shushu.<stage>` 让 mock 路由不歧义
- `shushu/llm.py` — DeepSeek (OpenAI 兼容) 客户端，`deepseek-chat` + `response_format=json_object`
- `shushu/render.py` — 把 4 段 JSON 拼成符合 aijobfit `PostShell` 的 `.tsx` + 一份原始 `.md` 副本
- `shushu/data/aijobfit_roles.json` — 14 角色 hard copy（来源 aijobfit `public/data/roles-domestic.json`）

## Commands

```bash
pip install -e ".[dev]"
export DEEPSEEK_API_KEY=sk-...
pytest                                          # mock LLM, 不打真实 API
python -m shushu.generate_case \\
  --input tests/fixtures/sample_project.md \\
  --target-role ai_engineer --out out/         # 真实 LLM E2E
```

## Tests

- `tests/conftest.py` 的 `FakeDeepSeekClient` 模拟 `chat.completions.create` 接口，按 `TASK_TAG` 路由 4 段固定 JSON
- `tests/test_generate_case.py::test_generated_tsx_parses_with_esbuild` 用 esbuild 做语法校验（不做类型检查，那是 aijobfit `tsc` 的事）
