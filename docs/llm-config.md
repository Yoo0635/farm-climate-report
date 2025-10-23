# LLM Configuration

## Environment Variables

- `OPENAI_API_KEY`: API key for LLM-1 (detailed report, RAG context)
- `GEMINI_API_KEY`: API key for LLM-2 (Korean-friendly refinement)
- `SOLAPI_ACCESS_KEY`, `SOLAPI_SECRET_KEY`, `SOLAPI_SENDER_NUMBER`: SMS provider credentials
- `DETAIL_BASE_URL`: Optional override for public detail links (defaults to Cloud Run URL)

## Setup Steps

1. Copy `.env.sample` to `.env` and fill in the values above.
2. Ensure the OpenAI account has access to vector store + `gpt-4.1-mini` (or configured model).
3. Enable Google Generative AI for Gemini and allow the `gemini-1.5-flash` model.
4. Verify SOLAPI sender number is registered and approved for SMS sending in Korea.
5. When deploying to Cloud Run, set these environment variables via `gcloud run deploy --set-secrets` or the Cloud Console.
