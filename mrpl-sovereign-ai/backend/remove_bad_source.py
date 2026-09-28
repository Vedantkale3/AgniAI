from app.rag.knowledge_base import _collection

results = _collection.get(where={"source": "sv600_m_automatic.pdf"})
ids_to_delete = results["ids"]

if ids_to_delete:
    _collection.delete(ids=ids_to_delete)
    print(f"Deleted {len(ids_to_delete)} chunks for sv600_m_automatic.pdf")
else:
    print("No chunks found for that source.")