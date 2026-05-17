from shushu_internship_tool.doc_knowledge import build_knowledge_base, query_knowledge


def test_doc_knowledge_returns_consistent_structure_and_query_hits() -> None:
    documents = [
        {
            "path": "business_overview.md",
            "title": "business_overview.md",
            "text": "票务履约流程包括回调、状态对账、异常补偿，团队关注状态一致性和处理效率。",
        }
    ]
    for mode in ("direct", "basic_rag", "knowledge_base"):
        base = build_knowledge_base(documents, mode=mode)
        assert base["mode"] == mode
        assert base["documents"]
        assert base["chunks"]

    base = build_knowledge_base(documents, mode="basic_rag")
    hits = query_knowledge(base, "异常补偿和状态一致性怎么做")
    assert hits
    assert "异常补偿" in hits[0]["text"]
