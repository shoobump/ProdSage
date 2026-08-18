import os
import chromadb
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

client = chromadb.PersistentClient(path='./chroma_db')
transcripts_collection = client.get_or_create_collection(name='podcast_transcripts')
guest_index_collection = client.get_or_create_collection(name='guest_index')

sarvam_client = SarvamAI(api_subscription_key=os.getenv('SARVAM_API_KEY'), timeout=60.0)


def call_with_retry(messages, retries=3):
    for attempt in range(retries):
        try:
            response = sarvam_client.chat.completions(messages=messages, model='sarvam-105b')
            content = response.choices[0].message.content
            if content and content.strip():
                return content
            print(f'  empty response, retry {attempt + 1}/{retries}...', flush=True)
        except Exception as e:
            print(f'  error: {e}, retry {attempt + 1}/{retries}...', flush=True)
    return None


def get_all_guests():
    all_data = transcripts_collection.get(include=['metadatas'])
    guests = set(m['guest'] for m in all_data['metadatas'])
    return sorted(guests)


def get_already_indexed():
    existing = guest_index_collection.get(include=[])
    return set(existing['ids'])


def get_sample_text_for_guest(guest, max_chunks=15):
    results = transcripts_collection.get(
        where={'guest': guest},
        limit=max_chunks,
        include=['documents']
    )
    return '\n\n'.join(results['documents'])


def summarize_guest(guest, sample_text):
    prompt = f'''Below are excerpts from a podcast interview with {guest}, a product/tech professional.

{sample_text[:6000]}

Write a short summary (3-5 sentences) covering: their core areas of expertise, the type of role or domain they specialize in (e.g. growth, platform, enterprise, leadership, B2C, B2B), and 5-8 key terms that best represent what they talk about.'''

    return call_with_retry([{'role': 'user', 'content': prompt}])


def run_guest_indexing():
    guests = get_all_guests()
    already_indexed = get_already_indexed()
    remaining = [g for g in guests if g not in already_indexed]

    print(f'Found {len(guests)} guests total, {len(already_indexed)} already indexed, {len(remaining)} remaining.', flush=True)

    failed = []

    for i, guest in enumerate(remaining):
        try:
            sample_text = get_sample_text_for_guest(guest)
            summary = summarize_guest(guest, sample_text)

            if summary is None:
                print(f'[{i + 1}/{len(remaining)}] SKIPPED {guest} (no valid response after retries)', flush=True)
                failed.append(guest)
                continue

            guest_index_collection.upsert(
                ids=[guest],
                documents=[summary],
                metadatas=[{'guest': guest}]
            )
            print(f'[{i + 1}/{len(remaining)}] Indexed {guest}', flush=True)

        except Exception as e:
            print(f'[{i + 1}/{len(remaining)}] ERROR on {guest}: {e}', flush=True)
            failed.append(guest)

    print(f'Guest index build complete. {len(failed)} failed: {failed}', flush=True)


if __name__ == '__main__':
    run_guest_indexing()