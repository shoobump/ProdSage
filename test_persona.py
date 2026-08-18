from persona import select_best_guest

company_profile = "A fast-growing B2B SaaS startup building collaboration tools for remote teams, known for a strong product-led growth motion."

job_description = "Looking for a Senior Product Manager to own the onboarding and activation funnel, drive self-serve growth, and work closely with data and engineering to improve conversion rates."

best_guest, chunks = select_best_guest(company_profile, job_description)

print(f'Best-fit interviewer: {best_guest}')
print()
print('Top supporting chunk:')
print(chunks[0][:400])