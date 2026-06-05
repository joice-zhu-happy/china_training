# Local Research Agent with Doubao Decision Loop

这是一个本地多源检索项目骨架。用户提出问题后，agent 会让 Doubao 模型决定下一步先搜索哪里、怎么搜索；拿到结果后再让模型继续推理并决定下一步，直到模型认为信息足够回答。

## 功能

- 本地 SQLite 数据库搜索
- 本地向量数据库搜索（轻量 JSON + 余弦相似度）
- 本地关键词搜索（倒排索引风格）
- 本地日志系统
- 本地 Git 代码仓库搜索
- 模拟企业内部系统 SDK
- Doubao/OpenAI-compatible 模型客户端
- 无 API Key 时自动使用本地模拟模型，方便演示流程

## 运行

```bash
pip install -r requirements.txt
python app.py
```

## 配置 Doubao

如果你的 Doubao 服务提供 OpenAI-compatible Chat Completions 接口，可以设置：

```powershell
$env:DOUBAO_API_KEY="你的 API Key"
$env:DOUBAO_BASE_URL="https://你的网关地址/v1"
$env:DOUBAO_MODEL="你的模型名"
python app.py
```

未配置时，项目会使用 `LocalMockModelClient`，它会按规则模拟“先搜哪里、再搜哪里、最后回答”的过程。

## 项目结构

```text
app.py
src/
  agent.py
  bootstrap.py
  config.py
  enterprise_sdk.py
  logging_system.py
  model_client.py
  search_tools.py
  storage.py
data/
  generated at runtime
logs/
  generated at runtime
```
