# shushu

shushu 不是简历生成器，是给 [aijobfit](https://github.com/LLM-X-Factorer/aijobfit) 应届分支生产示范案例文章的脚本。

输入：一份脱敏后的实习项目原始描述（`.md`）+ 目标角色 id（aijobfit 14 角色之一）。
输出：一篇可直接放进 `aijobfit/src/components/blog/posts/` 的 React 组件文件（`.tsx`）。

> aijobfit 侧的对接说明见 [aijobfit README · 案例文章生产](https://github.com/LLM-X-Factorer/aijobfit#案例文章生产)。

## 工作方式

由 LLM（DeepSeek `deepseek-chat`，OpenAI 兼容协议，prompt caching 服务端自动开启）驱动 4 步流水线：

1. 抽取：从原始描述拆出「背景 / 我的动作 / 技术细节 / 结果 / 缺失信息」
2. 命中扫描：对照目标角色的 `required_skills / preferred_skills` 找证据
3. 改写：生成「复盘版」（详细，给作者自己看）和「简历压缩版」（≤ 2 bullets）
4. 风险标注：列 3-5 个面试可能追问点 + 标准答法骨架

输出文件名 `${roleId}-${slug}.tsx`，套用 aijobfit `PostShell` 模板（`H2 / P / Ul / DataTable / Callout` 等 helper）。同时把原始抽取/扫描/改写/追问 JSON 写到 `raw/${roleId}-${slug}.md`，方便人工审阅。

## 与 aijobfit 的边界

简而言之：**aijobfit 是产品，shushu 是产品旁边一个写文章的小工具。** 不在同一个 runtime，不分享数据所有权。

|  | aijobfit | shushu |
|---|---|---|
| 形态 | Next.js Web App | Python 离线脚本 |
| 跑在哪 | 生产环境 (aijobfit.llmxfactor.cloud) | 维护者本地，一次性运行 |
| 谁用 | 求职用户 | aijobfit 维护者 / 受邀写手 |
| 网络拓扑 | 终端用户能访问 | 永远不上线，不被用户访问 |
| 数据所有权 | `roles-domestic.json` 的源 | hard copy，只读 |
| `.tsx` 文章所有权 | 文章最终落地的家 | 一次性生成器 |

两条单向同步线（手动）：

1. `aijobfit/public/data/roles-domestic.json` → `shushu/data/aijobfit_roles.json`（角色定义变化时重新覆盖，commit message 写来源 hash）
2. `shushu` 生成的 `out/*.tsx` → 人工审阅 + 补 `[待补：...]` → `aijobfit/src/components/blog/posts/`

边界规则：

- shushu **不读** agent-hunt、**不调** aijobfit 的 API、**不知道**用户存在
- aijobfit **不依赖** shushu；砍掉 shushu 仓库 aijobfit 照常运行，只是新文章得手写
- 角色定义冲突时 **aijobfit 说了算**；shushu 那份是 snapshot，过期就过期
- 生成的 `.tsx` 出问题：prompt / 模板的问题 → 改 shushu 重生成；单篇内容润色 / 数字补齐 → 直接在 aijobfit 那份手改，不回流
- PostShell API 变了：**先改 aijobfit，再来 shushu 改 `render.py`**，否则后续生成的 tsx 会 build 失败

shushu 明确**不做**：通用简历生成器 / runtime 服务 / 多角色路由 / RAG / 知识库 / 用户分析 / SEO（这些全归 aijobfit）。

## 快速开始

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"

export DEEPSEEK_API_KEY=sk-...

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
