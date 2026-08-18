import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_or_create_collection(name='podcast_transcripts')

query = "How do you prioritize features with limited engineering resources?"

results = collection.query(
    query_texts=[query],
    n_results=5
)

for i in range(len(results['documents'][0])):
    guest = results['metadatas'][0][i]['guest']
    chunk = results['documents'][0][i]
    print(f'--- Match {i+1} (guest: {guest}) ---')
    print(chunk[:300])
    print()