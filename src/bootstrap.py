from src.storage import LocalDatabase, LocalKeywordIndex, LocalVectorStore


DEMO_DOCUMENTS = [
    {
        "source": "policy",
        "title": "企业内部搜索系统设计原则",
        "content": "当用户问题不明确时，先使用向量搜索获取语义上下文，再使用关键词搜索确认术语。涉及员工、权限、工单时调用企业内部系统 SDK。",
    },
    {
        "source": "runbook",
        "title": "本地向量数据库说明",
        "content": "向量数据库适合查找语义相似内容，例如用户说报表不能下载，文档里可能写导出失败。",
    },
    {
        "source": "runbook",
        "title": "本地关键词搜索说明",
        "content": "关键词搜索适合精确匹配错误码、函数名、系统名称、人员名称、表名和配置项。",
    },
    {
        "source": "architecture",
        "title": "Agent 循环推理架构",
        "content": "模型每轮读取问题和历史搜索结果，决定下一步搜索源、查询词和理由。若信息足够，则输出最终答案。",
    },
    {
        "source": "integration",
        "title": "企业系统 SDK 使用方式",
        "content": "企业 SDK 可搜索工单、人员、权限和业务系统记录。CRM、IAM、财务系统问题通常优先查企业系统。",
    },
]


def bootstrap_demo_data():
    database = LocalDatabase()
    database.upsert_demo_documents(DEMO_DOCUMENTS)
    documents = database.all_documents()

    LocalVectorStore().build(documents)
    LocalKeywordIndex().build(documents)
