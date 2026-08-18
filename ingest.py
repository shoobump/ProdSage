import os
import chromadb

CHUNK_SIZE = 500  # words per chunk
CHUNK_OVERLAP = 50  # words of overlap between chunks

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
    # 'Ada Chen Rekhi.txt' -> 'Ada Chen Rekhi'
    return filename.replace('.txt', '').strip()

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_or_create_collection(name='podcast_transcripts')

transcript_dir = './transcripts'
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
        collection.add(
            ids=[f'chunk_{chunk_id}'],
            documents=[chunk],
            metadatas=[{'guest': guest, 'source_file': filename}]
        )
        chunk_id += 1

    print(f'Ingested {len(chunks)} chunks from {filename} (guest: {guest})')

print(f'Done. Total chunks in vector store: {chunk_id}')