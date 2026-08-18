from interview import start_interview, continue_interview

company_profile = "A fast-growing B2B SaaS startup building collaboration tools for remote teams, known for a strong product-led growth motion."

job_description = "Looking for a Senior Product Manager to own the onboarding and activation funnel, drive self-serve growth, and work closely with data and engineering to improve conversion rates."

cv_text = "Shubham Patel. 5+ years as a Senior PM in agritech. Led an AI co-pilot product (RAG-based) and a farm management platform. MBA from IIM-Ahmedabad."

guest, history, first_message = start_interview(company_profile, job_description, cv_text)

print(f'Interviewer: {guest}')
print()
print(f'Bot: {first_message}')
print()

user_answer = "Sure — I'd start by looking at the funnel data to find the biggest drop-off point, then run qualitative interviews with users who churned right after that step."

history, reply = continue_interview(history, user_answer)

print(f'You: {user_answer}')
print()
print(f'Bot: {reply}')