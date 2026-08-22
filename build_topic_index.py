import os
import json
import chromadb
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

client = chromadb.PersistentClient(path='./chroma_db')
topic_knowledge_collection = client.get_or_create_collection(name='topic_knowledge')

sarvam_client = SarvamAI(api_subscription_key=os.getenv('SARVAM_API_KEY'), timeout=90.0)

TRANSCRIPT_DIR = './transcripts'


def call_with_retry(messages, retries=3):
    for attempt in range(retries):
        try:
            response = sarvam_client.chat.completions(
                messages=messages,
                model='sarvam-105b',
                max_tokens=4096,
                reasoning_effort=None
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content
            print(f'  empty response, retry {attempt + 1}/{retries}...', flush=True)
        except Exception as e:
            print(f'  error: {e}, retry {attempt + 1}/{retries}...', flush=True)
    return None


def get_all_guests():
    files = [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith('.txt')]
    return sorted(f.replace('.txt', '') for f in files)


def already_indexed_guests():
    all_data = topic_knowledge_collection.get(include=['metadatas'])
    return set(m['guest'] for m in all_data['metadatas'])


def extract_topics(guest_name, full_text):
    # Cap extremely long transcripts to stay within a safe prompt size
    # (Sarvam-105b has a 128k token context, this is a conservative cap)
    text = full_text[:60000]

    prompt = f'''Below is a full podcast interview transcript with {guest_name}, a product management professional.

TRANSCRIPT:
{text}

Extract the distinct, substantive topics {guest_name} discusses in this conversation (typically 4-10 topics). For EACH topic, write a thorough 4-8 sentence learning summary that synthesizes everything meaningful they said about it across the WHOLE conversation — not just one quote, but the full arc of their point, including any examples or frameworks they mention.

Skip trivial or passing mentions. Only include topics with real substance.

Respond with ONLY valid JSON, no other text, no markdown code fences, in this exact format:
[
  {{"topic": "short topic name", "summary": "the synthesized summary"}}
]'''

    raw = call_with_retry([{'role': 'user', 'content': prompt}])
    if raw is None:
        return None

    cleaned = raw.strip()
    if cleaned.startswith('```'):
        parts = cleaned.split('```')
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.startswith('json'):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f'  Could not parse JSON for {guest_name}', flush=True)
        return None


def run_topic_indexing():
    guests = get_all_guests()
    already_done = already_indexed_guests()
    remaining = [g for g in guests if g not in already_done]

    print(f'Found {len(guests)} guests, {len(already_done)} already indexed, {len(remaining)} remaining.', flush=True)

    failed = []
    entry_id_counter = 0

    for i, guest in enumerate(remaining):
        filepath = os.path.join(TRANSCRIPT_DIR, f'{guest}.txt')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                full_text = f.read()
        except FileNotFoundError:
            print(f'[{i + 1}/{len(remaining)}] SKIPPED {guest} (file not found)', flush=True)
            failed.append(guest)
            continue

        topics = extract_topics(guest, full_text)

        if not topics:
            print(f'[{i + 1}/{len(remaining)}] FAILED {guest} (no valid topics extracted)', flush=True)
            failed.append(guest)
            continue

        for t in topics:
            topic_name = str(t.get('topic', '')).strip()
            summary = str(t.get('summary', '')).strip()
            if not topic_name or not summary:
                continue

            doc_text = f'{topic_name}: {summary}'
            topic_knowledge_collection.add(
                ids=[f'{guest}__{entry_id_counter}'],
                documents=[doc_text],
                metadatas=[{'guest': guest, 'topic': topic_name, 'summary': summary}]
            )
            entry_id_counter += 1

        print(f'[{i + 1}/{len(remaining)}] Indexed {guest} ({len(topics)} topics)', flush=True)

    print(f'Topic index build complete. {len(failed)} failed: {failed}', flush=True)


if __name__ == '__main__':
    run_topic_indexing()