from persona import client as chroma_client, guest_index_collection

topic_knowledge_collection = chroma_client.get_or_create_collection(name='topic_knowledge')


def search_topics(query, max_results=8):
    """Search the precomputed topic knowledge base directly — clean,
    synthesized concepts, no live synthesis call needed."""
    results = topic_knowledge_collection.query(query_texts=[query], n_results=max_results)

    metadatas = results['metadatas'][0]
    seen = set()
    picks = []
    for m in metadatas:
        key = (m['guest'], m['topic'])
        if key in seen:
            continue
        seen.add(key)
        picks.append({'guest': m['guest'], 'topic': m['topic'], 'summary': m['summary']})

    return picks


def search_experts(query, n=8):
    """Search the per-guest summary index to find experts matching a theme."""
    results = guest_index_collection.query(query_texts=[query], n_results=n)
    guest_metas = results['metadatas'][0]
    summaries = results['documents'][0]

    return [{'guest': g['guest'], 'summary': s} for g, s in zip(guest_metas, summaries)]


def get_expert_reading(guest_name):
    """Return this guest's full set of topic-knowledge entries — clean,
    synthesized concepts rather than raw transcript excerpts."""
    results = topic_knowledge_collection.get(
        where={'guest': guest_name},
        include=['metadatas']
    )
    entries = [{'topic': m['topic'], 'summary': m['summary']} for m in results['metadatas']]
    return entries


def get_all_topics():
    """Full list of distinct topic names — used for autocomplete-style suggestions."""
    all_data = topic_knowledge_collection.get(include=['metadatas'])
    return sorted(set(m['topic'] for m in all_data['metadatas']))


def get_all_guest_names():
    """Full list of guest names."""
    all_data = guest_index_collection.get(include=[])
    return sorted(all_data['ids'])