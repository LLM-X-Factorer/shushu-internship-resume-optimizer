# Contributing

Thanks for your interest in improving `shushu`.

## Scope

`shushu` 只做一件事：把一份脱敏后的实习项目描述 + 一个 aijobfit 角色 id，生成一篇可直接 import 到 `aijobfit/src/components/blog/posts/` 的 `.tsx`。

不要把它扩展成通用简历工具 / 多角色路由器 / RAG 知识库。如果想做这类东西，请在 aijobfit 主仓里另起项目。

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run Tests

```bash
pytest
```

测试默认 mock 掉 LLM 调用（OpenAI 兼容接口）；不会真的请求 DeepSeek。

## 改 prompt 时

`shushu/prompts.py` 里的硬约束（不编造数字 / 禁用词清单 / bullet 结构 / 答法骨架格式）是产品契约的一部分，不要在没和 aijobfit 维护者对齐前删改。新增约束 OK；放宽现有约束需要在 PR 里给出证据。

## 改角色数据时

`shushu/data/aijobfit_roles.json` 是 aijobfit `roles-domestic.json` 的 hard copy。直接手写覆盖请在 commit message 里写明来源 commit hash。

## Privacy

不要提交：

- 真实公司 / 产品 / 客户名
- 真实指标、用户数据、内部文档
- 含密钥的配置

测试 fixture 必须是完全虚构的脱敏样本。
