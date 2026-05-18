from __future__ import annotations

import json
from textwrap import dedent


SYSTEM_PROMPT = dedent(
    """\
    你是 shushu，一个为 aijobfit 应届分支生产示范案例的写作助手。

    输出对象：aijobfit 站点 /blog/<slug> 上一篇展示给应届求职者看的实战复盘文章，主角是「一位匿名应届实习生在脱敏项目里的真实动作」。

    硬性约束（违反一次就算输出失败，重新写）：

    - 不编造任何数字。原始材料里没有的指标、人数、金额、时长、并发量、转化率、覆盖率，一律写成 `[待补：xx 类指标]`。
    - 不使用以下词及其同义改写：赋能、全链路、闭环、降本增效、打通、大幅、显著、深度、底层、生态、抓手、对齐颗粒度、迭代飞轮。
    - 不写「显著提升」「大幅优化」「极大改善」「成功落地」「平稳上线」一类没有数字支撑的形容词。
    - 任何信息缺失就显式 `[待补：...]`，不要用「相关」「一系列」「若干」糊过去。
    - 简历版每条 bullet 必须包含：1 个具体动词 + 1 个量化或 `[待补：...]` + 1 个业务上下文。
    - 复盘版可以更长，但仍只写真实做过的事；不要补「学到了 X」「明白了 Y」一类反思腔。
    - 面试追问的「标准答法骨架」只给框架（先答 X、再补 Y、最后落到 Z），不要替候选人编内容。
    - 全部输出使用中文，保留英文技术术语原文（FastAPI、Kafka、RAG、Embedding、LangChain 等）。

    输出格式：严格输出一个 JSON 对象，字段名固定，不要写额外解释、Markdown 代码围栏或前后缀。
    """
)


def extract_prompt(raw_input: str) -> str:
    return dedent(
        f"""\
        TASK_TAG: shushu.extract
        任务：从下面这段脱敏后的实习项目原始描述里抽取结构化信息。

        要抽的字段（用 JSON 输出）：
        - background: 业务背景（这是什么产品 / 谁在用 / 解决什么真实问题），3-5 句
        - my_actions: 我具体做了哪些事（按时间或模块分条），每条一句话，动词开头
        - tech_details: 技术细节（用了什么栈 / 如何接的 / 数据流是怎样的），按要点分条
        - results: 结果与产出（指标、上线情况、对业务的影响），如果原文没数字，就把这一条写成 `[待补：xx 类指标]`
        - missing_info: 原文没说清的关键信息（缺哪些数字、缺哪些上下文、哪些边界没交代），按追问角度分条

        原始描述：
        ```
        {raw_input}
        ```

        只输出 JSON：{{"background": str, "my_actions": [str], "tech_details": [str], "results": [str], "missing_info": [str]}}
        """
    )


def scan_prompt(extracted_json: dict, role: dict) -> str:
    role_block = {
        "role_id": role["role_id"],
        "role_name": role["role_name"],
        "required_skills": role["required_skills"],
        "preferred_skills": role["preferred_skills"],
    }
    return dedent(
        f"""\
        TASK_TAG: shushu.scan
        任务：把上一步抽出来的实习经历，对照 aijobfit 角色「{role['role_name']}」({role['role_id']}) 的技能清单做命中扫描。

        角色技能清单（来自 aijobfit roles-domestic.json，required 比 preferred 重要）：
        ```
        {json.dumps(role_block, ensure_ascii=False, indent=2)}
        ```

        抽取结果：
        ```
        {json.dumps(extracted_json, ensure_ascii=False, indent=2)}
        ```

        判断每条 required_skills / preferred_skills 在这段经历里是否真的有证据。证据必须能指向 my_actions 或 tech_details 中的一条具体内容，不能仅凭关键词联想。

        只输出 JSON：
        {{
          "hits": [{{"skill_id": str, "evidence": str, "strength": "strong"|"medium"|"weak"}}],
          "misses": [{{"skill_id": str, "reason": str}}],
          "summary": str  // 一句话总结这段经历对该角色的契合度，不夸大不贬低
        }}
        """
    )


def rewrite_prompt(extracted_json: dict, scan_json: dict, role: dict) -> str:
    return dedent(
        f"""\
        TASK_TAG: shushu.rewrite
        任务：基于抽取结果 + 命中扫描，写两个版本的项目描述。

        目标角色：{role['role_name']} ({role['role_id']})

        抽取结果：
        ```
        {json.dumps(extracted_json, ensure_ascii=False, indent=2)}
        ```

        命中扫描：
        ```
        {json.dumps(scan_json, ensure_ascii=False, indent=2)}
        ```

        版本 1 - 复盘版（review）：给作者本人和读者看的详细复盘，分成「背景」「我的动作」「技术细节」「结果」四段，每段 3-6 句。允许写权衡和踩坑，但不写反思鸡汤。

        版本 2 - 简历压缩版（resume）：≤ 2 条 bullet，单条 ≤ 35 个中文字符。每条 bullet 强制结构「动词 + 量化或 [待补：...] + 业务上下文」。优先写在命中扫描里 strength=strong 的技能对应的事。

        只输出 JSON：
        {{
          "review": {{
            "background": str,
            "my_actions": str,
            "tech_details": str,
            "results": str
          }},
          "resume_bullets": [str, str]
        }}
        """
    )


def risk_prompt(extracted_json: dict, rewrite_json: dict, role: dict) -> str:
    return dedent(
        f"""\
        TASK_TAG: shushu.risk
        任务：作为面试官，列出 3-5 个最可能被追问的点，并给出标准答法骨架。

        目标角色：{role['role_name']} ({role['role_id']})

        抽取结果：
        ```
        {json.dumps(extracted_json, ensure_ascii=False, indent=2)}
        ```

        改写后的描述：
        ```
        {json.dumps(rewrite_json, ensure_ascii=False, indent=2)}
        ```

        每个追问的「骨架」格式：先答 X，再补 Y，最后落到 Z。不要替候选人编具体内容，骨架只是告诉他「应该按什么顺序展开」。

        只输出 JSON：
        {{
          "follow_ups": [
            {{"question": str, "why_asked": str, "answer_skeleton": str}}
          ]
        }}
        """
    )
