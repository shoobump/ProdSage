import os

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += size - overlap
    return chunks

def guest_name_from_filename(filename):
    return filename.replace('.txt', '').strip()

def run_ingestion(collection, transcript_dir='./transcripts', batch_size=100):
    all_ids = []
    all_documents = []
    all_metadatas = []
    chunk_id = 0

    for filename in os.listdir(transcript_dir):
        if not filename.endswith('.txt'):
            continue
        filepath = os.path.join(transcript_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        guest = guest_name_from_filename(filename)
        chunks = chunk_text(text)

        for chunk in chunks:
            all_ids.append(f'chunk_{chunk_id}')
            all_documents.append(chunk)
            all_metadatas.append({'guest': guest, 'source_file': filename})
            chunk_id += 1

        print(f'Prepared {len(chunks)} chunks from {filename} (guest: {guest})', flush=True)

    print(f'Adding {chunk_id} chunks to vector store in batches of {batch_size}...', flush=True)

    for i in range(0, len(all_ids), batch_size):
        collection.add(
            ids=all_ids[i:i+batch_size],
            documents=all_documents[i:i+batch_size],
            metadatas=all_metadatas[i:i+batch_size]
        )
        print(f'  ...{min(i+batch_size, chunk_id)}/{chunk_id} added', flush=True)

    print(f'Done. Total chunks in vector store: {chunk_id}', flush=True)

if __name__ == '__main__':
    import chromadb
    client = chromadb.PersistentClient(path='./chroma_db')
    collection = client.get_or_create_collection(name='podcast_transcripts')
    run_ingestion(collection)