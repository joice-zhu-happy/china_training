from src.config import MAX_AGENT_STEPS
from src.logging_system import get_logger
from src.model_client import DoubaoModelClient
from src.search_tools import SearchTools


class ResearchAgent:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.model = DoubaoModelClient()
        self.tools = SearchTools()

    def answer(self, question):
        history = []

        for step in range(1, MAX_AGENT_STEPS + 1):
            decision = self.model.decide(question, history)
            self.logger.info("step=%s decision=%s", step, decision)

            action = decision.get("action")
            if action == "answer":
                return decision.get("answer", "模型认为信息足够，但没有生成回答。")

            if action != "search":
                return f"模型返回了无法识别的动作: {decision}"

            source = decision.get("source")
            query = decision.get("query", question)
            results = self.tools.search(source, query)

            history.append(
                {
                    "step": step,
                    "decision": decision,
                    "results": results,
                }
            )

        return self._fallback_answer(question, history)

    def _fallback_answer(self, question, history):
        self.logger.warning("max steps reached question=%s", question)
        return (
            "已经达到最大搜索轮数，以下是目前收集到的信息。\n\n"
            f"问题: {question}\n"
            f"搜索轮数: {len(history)}\n"
            "建议提高 MAX_AGENT_STEPS 或缩小问题范围。"
        )
