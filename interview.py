import os
from dotenv import load_dotenv
from sarvamai import SarvamAI
from persona import select_best_guest, get_persona_context

load_dotenv()

client = SarvamAI(api_subscription_key=os.getenv('SARVAM_API_KEY'), timeout=60.0)


def call_with_retry(messages, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            return client.chat.completions(messages=messages, model="sarvam-105b")
        except Exception as e:
            last_error = e
            print(f'Request failed (attempt {attempt + 1}/{retries}), retrying...')
    raise last_error


def build_system_prompt(guest_name, sample_chunks, company_profile, job_description, cv_text):
    sample_material = '\n\n'.join(sample_chunks[:5])

    system_prompt = f'''You are role-playing as {guest_name}, a product management expert, conducting a mock job interview.

Below are real excerpts of how {guest_name} thinks and talks, drawn from a podcast interview. Use these to match their tone, philosophy, and areas of expertise — do not invent opinions that contradict this material.

--- REAL TRANSCRIPT EXCERPTS FROM {guest_name} ---
{sample_material}
--- END EXCERPTS ---

You are interviewing a candidate for this role:

COMPANY PROFILE:
{company_profile}

JOB DESCRIPTION:
{job_description}

CANDIDATE'S CV:
{cv_text}

Instructions:
- Talk like a real, respectful professional in a live conversation, not an AI assistant. Skip empty praise-cushioning ("That's a solid approach", "Great point", "I love that") — but stay warm and human, the way a genuinely engaged interviewer would, not clipped or curt.
- Being direct is good. Being terse or dismissive is not. You can disagree, push back, or ask a sharper follow-up — just do it the way a respectful colleague would, not like you're testing someone's patience.
- Keep responses SHORT: 2-4 sentences most of the time. This is spoken conversation, not a written review.
- Ask ONE question at a time. Never stack two questions in one turn.
- Don't drill on a single thread indefinitely. After roughly 3-4 exchanges on one topic (including follow-ups), wrap that thread with a brief acknowledgment and move to a genuinely different area — e.g. if you've been probing a diagnosis/experimentation topic, switch to something like stakeholder conflict, a past failure, prioritization trade-offs, or a leadership scenario.
- Over the course of the interview, aim to cover a spread of different PM competencies (product sense, execution/metrics, stakeholder/leadership, strategy) rather than exhausting one scenario. Treat this like a real 30-45 minute interview with several distinct question areas, not one long case study.
- Introduce yourself by name ({guest_name}) in your opening greeting, like a real interviewer would.
- Find the candidate's name in their CV below and address them by their first name at least once early in the conversation, the way a person naturally would — not in every single turn.
- Reference the candidate's actual CV background naturally, the way a person would bring up something they noticed, not "I see from your CV that...".
- Do not summarize, recap, or explain what you're about to do ("Now I'm going to ask about..."). Just ask it.
- Stay in {guest_name}'s actual voice and vocabulary from the excerpts above, including their level of formality/casualness — but keep it conversational and collegial in tone, not blunt.
- Start now with a short, warm, casual greeting and your first question. No long preamble.'''

    return system_prompt


def start_interview(company_profile, job_description, cv_text):
    best_guest, sample_chunks = select_best_guest(company_profile, job_description)
    system_prompt = build_system_prompt(best_guest, sample_chunks, company_profile, job_description, cv_text)

    history = [{'role': 'system', 'content': system_prompt}]

    response = call_with_retry(history)
    first_message = response.choices[0].message.content

    history.append({'role': 'assistant', 'content': first_message})

    return best_guest, history, first_message, sample_chunks


def continue_interview(history, user_message):
    history.append({'role': 'user', 'content': user_message})

    response = call_with_retry(history)
    reply = response.choices[0].message.content

    history.append({'role': 'assistant', 'content': reply})

    return history, reply


def generate_debrief(guest_name, history, sample_chunks):
    sample_material = '\n\n'.join(sample_chunks[:5])

    debrief_prompt = f'''The mock interview is now over. Based on the full conversation above, write a debrief as {guest_name} would genuinely give a candidate afterward.

Ground your evaluation in how {guest_name} actually thinks, based on these excerpts of their real interview style:
{sample_material}

Structure your debrief with these sections:
1. **What worked** — 2-3 specific strengths from the candidate's actual answers, referencing what they actually said
2. **What to sharpen** — 2-3 specific gaps or missed opportunities, referencing what they actually said
3. **How I'd evaluate this** — a short, honest read on how this would likely land in a real interview at this stage

Be specific and reference actual moments from the conversation — avoid generic feedback. Keep the tone consistent with {guest_name}'s voice: direct but respectful, not a cheerleader.'''

    debrief_history = history + [{'role': 'user', 'content': debrief_prompt}]
    response = call_with_retry(debrief_history)
    return response.choices[0].message.content


def start_interview_with_guest(guest_name, company_profile, job_description, cv_text):
    sample_chunks = get_persona_context(guest_name, f'{company_profile}\n\n{job_description}', n_results=8)
    system_prompt = build_system_prompt(guest_name, sample_chunks, company_profile, job_description, cv_text)

    history = [{'role': 'system', 'content': system_prompt}]
    response = call_with_retry(history)
    first_message = response.choices[0].message.content
    history.append({'role': 'assistant', 'content': first_message})

    return guest_name, history, first_message, sample_chunks


def generate_quick_feedback(guest_name, user_answer, sample_chunks):
    sample_material = '\n\n'.join(sample_chunks[:3])

    prompt = f'''You are {guest_name}, jotting a quick private note to yourself about the candidate's last answer — they won't see this live, it's not spoken.

Candidate's last answer: "{user_answer}"

Style reference for how {guest_name} thinks:
{sample_material}

Write ONE short, specific observation (1-2 sentences max) about THIS SPECIFIC answer. Note a genuine strength or a genuine gap — something concrete tied to what they actually said. Generic praise like "good answer" is not allowed. Just the note, no preamble.'''

    response = call_with_retry([{'role': 'user', 'content': prompt}])
    return response.choices[0].message.content