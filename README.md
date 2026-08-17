**PM Interview Practice Bot**

A conversational mock-interview tool that helps you practice for Product Manager interviews by simulating conversations with expert PM voices — grounded in real transcripts from Lenny's Podcast.


**How it works**

Ingest — Podcast transcripts are chunked and embedded into a searchable vector store (Chroma), tagged by guest.

Intake — You provide a target company profile, job description, and your CV.

Persona match — The system retrieves the most relevant guest(s) and topics for that role, and builds an interviewer persona grounded in their real frameworks and style.

Interview — A conversational loop: the bot asks role-specific questions, follows up on your answers, and gives a structured debrief at the end — referencing how that expert would actually evaluate your response.


**Stack**

LLM: Sarvam-105B (via Sarvam AI API)

Vector store: Chroma

UI: Streamlit

Hosting: Streamlit Community Cloud

Language: Python


**Status**

🚧 In development — currently building the transcript ingestion and retrieval pipeline.

Planned next: text-based mock interviews, followed by a voice mode using Sarvam's Speech-to-Text and Text-to-Speech APIs.


**Why this exists**

Built as a hands-on project to learn RAG-based application development, and as a personal tool to prepare for Product Manager interviews.
