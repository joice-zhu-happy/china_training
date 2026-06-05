class MockEnterpriseSDK:
    """A simulated internal enterprise system SDK."""

    def __init__(self):
        self.tickets = [
            {
                "id": "INC-1001",
                "title": "财务报表导出失败",
                "status": "resolved",
                "detail": "原因是权限组缺少 finance_report_export，已通过 IAM 模板修复。",
            },
            {
                "id": "REQ-2048",
                "title": "客户 360 数据同步延迟",
                "status": "open",
                "detail": "CRM 到数据湖的同步延迟约 20 分钟，建议先检查 integration_batch_job。",
            },
            {
                "id": "KB-3310",
                "title": "内部搜索系统排障手册",
                "status": "published",
                "detail": "关键词无结果时应先检查分词、索引更新时间和数据源权限。",
            },
        ]

        self.people = [
            {
                "name": "Alice Zhang",
                "team": "Data Platform",
                "expertise": "vector search, SQLite, ETL",
            },
            {
                "name": "Ben Li",
                "team": "Enterprise Apps",
                "expertise": "CRM SDK, IAM, workflow automation",
            },
        ]

    def search_tickets(self, query, limit=5):
        return self._search(self.tickets, query, limit)

    def search_people(self, query, limit=5):
        return self._search(self.people, query, limit)

    def _search(self, items, query, limit):
        query_lower = query.lower()
        results = []

        for item in items:
            text = " ".join(str(value) for value in item.values()).lower()
            if any(token in text for token in query_lower.split()):
                results.append(item)

        return results[:limit]
