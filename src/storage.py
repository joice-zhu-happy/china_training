import json
import math
import re
import sqlite3
from collections import Counter, defaultdict

from src.config import KEYWORD_INDEX_PATH, SQLITE_PATH, VECTOR_PATH


def tokenize(text):
    raw_tokens = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]+", text.lower())
    tokens = []

    for token in raw_tokens:
        tokens.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            tokens.extend(token[index : index + 2] for index in range(len(token) - 1))

    return tokens


def text_vector(text):
    tokens = tokenize(text)
    counts = Counter(tokens)
    length = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {token: value / length for token, value in counts.items()}


def cosine_similarity(left, right):
    return sum(left.get(token, 0.0) * right.get(token, 0.0) for token in left)


class LocalDatabase:
    def __init__(self, path=SQLITE_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self):
        return sqlite3.connect(self.path)

    def _init_schema(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL
                )
                """
            )

    def upsert_demo_documents(self, documents):
        with self.connect() as conn:
            existing = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            if existing:
                return

            conn.executemany(
                "INSERT INTO documents(source, title, content) VALUES (?, ?, ?)",
                [(doc["source"], doc["title"], doc["content"]) for doc in documents],
            )

    def all_documents(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, source, title, content FROM documents ORDER BY id"
            ).fetchall()

        return [
            {"id": row[0], "source": row[1], "title": row[2], "content": row[3]}
            for row in rows
        ]

    def search(self, query, limit=5):
        query_tokens = set(tokenize(query))
        results = []

        for doc in self.all_documents():
            score = sum(1 for token in query_tokens if token in tokenize(doc["content"]))
            score += sum(1 for token in query_tokens if token in tokenize(doc["title"]))

            if score:
                results.append({**doc, "score": score})

        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


class LocalVectorStore:
    def __init__(self, path=VECTOR_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def build(self, documents):
        payload = [
            {
                "id": doc["id"],
                "source": doc["source"],
                "title": doc["title"],
                "content": doc["content"],
                "vector": text_vector(f"{doc['title']} {doc['content']}"),
            }
            for doc in documents
        ]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")

    def search(self, query, limit=5):
        if not self.path.exists():
            return []

        query_vector = text_vector(query)
        documents = json.loads(self.path.read_text("utf-8"))
        results = []

        for doc in documents:
            score = cosine_similarity(query_vector, doc["vector"])
            if score > 0:
                results.append(
                    {
                        "id": doc["id"],
                        "source": doc["source"],
                        "title": doc["title"],
                        "content": doc["content"],
                        "score": round(score, 4),
                    }
                )

        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


class LocalKeywordIndex:
    def __init__(self, path=KEYWORD_INDEX_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def build(self, documents):
        index = defaultdict(list)

        for doc in documents:
            for token in set(tokenize(f"{doc['title']} {doc['content']}")):
                index[token].append(doc["id"])

        payload = {"index": index, "documents": {str(doc["id"]): doc for doc in documents}}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")

    def search(self, query, limit=5):
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text("utf-8"))
        query_tokens = tokenize(query)
        scores = Counter()

        for token in query_tokens:
            for doc_id in payload["index"].get(token, []):
                scores[str(doc_id)] += 1

        results = []
        for doc_id, score in scores.most_common(limit):
            doc = payload["documents"][doc_id]
            results.append({**doc, "score": score})

        return results
