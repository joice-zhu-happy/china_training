import json
import re
import urllib.error
import urllib.request

from src.config import DOUBAO_API_KEY, DOUBAO_BASE_URL, DOUBAO_MODEL


SYSTEM_PROMPT = """
你是一个企业内部研究 agent 的规划大脑。
你可以使用这些搜索源:
- database: 本地 SQLite 结构化文档
- vector: 本地向量数据库，适合语义相近但关键词不完全一致的问题
- keyword: 本地关键词搜索，适合精确术语、错误码、人名、系统名
- code: 本地 Git 代码仓库搜索，适合查代码、配置、函数、实现细节
- enterprise: 模拟企业内部系统 SDK，适合查工单、人员、业务系统记录

每一轮必须只输出 JSON，不要输出 Markdown。
如果还需要搜索，输出:
{"action":"search","source":"vector","query":"要搜索的内容","reason":"为什么搜这里"}

如果信息已经足够回答，输出:
{"action":"answer","answer":"给用户的最终中文回答"}
""".strip()


class DoubaoModelClient:
    def __init__(self):
        self.enabled = bool(DOUBAO_API_KEY and DOUBAO_BASE_URL)

    def decide(self, question, history):
        if not self.enabled:
            return LocalMockModelClient().decide(question, history)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"question": question, "search_history": history},
                    ensure_ascii=False,
                ),
            },
        ]

        request = urllib.request.Request(
            f"{DOUBAO_BASE_URL.rstrip('/')}/chat/completions",
            data=json.dumps(
                {
                    "model": DOUBAO_MODEL,
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {DOUBAO_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Doubao API request failed: {exc.code} {detail}") from exc

        content = payload["choices"][0]["message"]["content"]
        return parse_json(content)


class LocalMockModelClient:
    """Rule-based local stand-in so the project works without an API key."""

    def decide(self, question, history):
        searched_sources = {item["decision"]["source"] for item in history}
        question_lower = question.lower()

        if not history:
            if any(token in question_lower for token in ["代码", "函数", "config", "app.py"]):
                return self.search("code", question, "问题看起来和代码仓库有关。")
            if any(token in question_lower for token in ["工单", "员工", "权限", "crm", "iam"]):
                return self.search("enterprise", question, "问题看起来和企业系统记录有关。")
            return self.search("vector", question, "先用语义检索获得宽泛上下文。")

        if "keyword" not in searched_sources:
            return self.search("keyword", question, "用关键词检索补充精确匹配。")

        if "database" not in searched_sources:
            return self.search("database", question, "检查结构化本地数据库。")

        if "enterprise" not in searched_sources and any(
            token in question_lower for token in ["工单", "权限", "系统", "crm", "iam"]
        ):
            return self.search("enterprise", question, "补充企业内部系统记录。")

        return {
            "action": "answer",
            "answer": self.compose_answer(question, history),
        }

    def search(self, source, query, reason):
        return {
            "action": "search",
            "source": source,
            "query": query,
            "reason": reason,
        }

    def compose_answer(self, question, history):
        lines = [f"问题: {question}", "", "根据本地多源检索，找到的信息如下:"]

        for step_number, item in enumerate(history, start=1):
            decision = item["decision"]
            results = item["results"]
            lines.append(
                f"{step_number}. 来源 {decision['source']}，搜索 `{decision['query']}`，原因: {decision['reason']}"
            )
            lines.append(f"   结果摘要: {summarize_result(results)}")

        lines.append("")
        lines.append("结论: 上述结果已经足够形成初步回答。真实接入 Doubao 后，这里会由模型基于检索结果生成更自然、更完整的答案。")
        return "\n".join(lines)


def parse_json(content):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def summarize_result(results):
    text = json.dumps(results, ensure_ascii=False)
    return text[:300] + ("..." if len(text) > 300 else "")
