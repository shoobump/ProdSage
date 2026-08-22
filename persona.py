import os
import tarfile
import urllib.request
import chromadb
from collections import defaultdict

VECTOR_STORE_URL = 'https://github.com/shoobump/ProdSage/releases/download/v2.0-vectorstore/chroma_db.tar.gz'

def ensure_vector_store():
    if os.path.exists('./chroma_db'):
        return

    print('chroma_db not found locally — downloading prebuilt store...', flush=True)
    urllib.request.urlretrieve(VECTOR_STORE_URL, 'chroma_db.tar.gz')
    print('Download complete. Extracting...', flush=True)

    with tarfile.open('chroma_db.tar.gz', 'r:gz') as tar:
        tar.extractall('.')

    os.remove('chroma_db.tar.gz')
    print('Vector store ready.', flush=True)

ensure_vector_store()

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_or_create_collection(name='podcast_transcripts')
guest_index_collection = client.get_or_create_collection(name='guest_index')


def select_best_guest(company_profile, job_description):
    query = f"{company_profile}\n\n{job_description}"

    if guest_index_collection.count() > 0:
        results = guest_index_collection.query(
            query_texts=[query],
            n_results=1
        )
        best_guest = results['metadatas'][0][0]['guest']
        sample_chunks = get_persona_context(best_guest, query, n_results=5)
        return best_guest, sample_chunks

    results = collection.query(query_texts=[query], n_results=30)

    guest_scores = defaultdict(float)
    guest_chunks = defaultdict(list)

    distances = results['distances'][0]
    metadatas = results['metadatas'][0]
    documents = results['documents'][0]

    for i in range(len(metadatas)):
        guest = metadatas[i]['guest']
        score = 1 - distances[i]
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


def get_top_guests(company_profile, job_description, n=4):
    query = f'{company_profile}\n\n{job_description}'
    results = guest_index_collection.query(query_texts=[query], n_results=n)
    return [m['guest'] for m in results['metadatas'][0]]