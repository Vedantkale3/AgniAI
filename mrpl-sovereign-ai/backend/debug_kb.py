from app.rag.knowledge_base import query_knowledge_base

hits = query_knowledge_base("valve", top_k=37, min_relevance=-1)

sv600_hits = [h for h in hits if "sv600" in h["source"].lower()]

if not sv600_hits:
    print("No chunk with source containing 'sv600' was found at all.")
else:
    for hit in sv600_hits:
        print("SOURCE:", hit["source"])
        print("RELEVANCE:", hit["relevance"])
        print("TEXT LENGTH:", len(hit["text"]))
        print("TEXT PREVIEW:")
        print(hit["text"])
        print("-" * 60)