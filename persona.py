import os
import chromadb
from collections import defaultdict

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_or_create_collection(name='podcast_transcripts')

EXPECTED_MIN_CHUNKS = 10000  # rough floor — real count is ~11,617

if collection.count() < EXPECTED_MIN_CHUNKS:
    print(f'Vector store incomplete ({collection.count()} chunks) — rebuilding...')
    client.delete_collection('podcast_transcripts')
    collection = client.get_or_create_collection(name='podcast_transcripts')
    print('Vector store is empty — running ingestion...')
    from ingest import run_ingestion
    run_ingestion(collection)

def select_best_guest(company_profile, job_description):
    query = f"{company_profile}\n\n{job_description}"

    results = collection.query(
        query_texts=[query],
        n_results=30
    )

    guest_scores = defaultdict(float)
    guest_chunks = defaultdict(list)

    distances = results['distances'][0]
    metadatas = results['metadatas'][0]
    documents = results['documents'][0]

    for i in range(len(metadatas)):
        guest = metadatas[i]['guest']
        score = 1 - distances[i]  # smaller distance = more relevant, so flip it
        guest_scores[guest] += score
        guest_chunks[guest].append(documents[i])

    best_guest = max(guest_scores, key=guest_scores.get)
    return best_guest, guest_chunks[best_guest]


def get_persona_context(guest_name, topic_query, n_results=8):
    results = collection.query(
        query_texts=[topic_query],
        n_results=n_results,
        where={'guest': guest_name}
    )
    return results['documents'][0]