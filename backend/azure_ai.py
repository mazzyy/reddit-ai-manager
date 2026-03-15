"""
Azure OpenAI integration — content generation pipeline.
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPTS = {
    "reddit_post": """You are an expert social media content strategist specializing in Reddit.
Your job is to take a user's raw idea or draft and transform it into an engaging,
authentic Reddit post that fits the culture of the target subreddit(s).

Rules:
- Write in a natural, conversational tone — Reddit users detect corporate/AI speak instantly.
- Use the subreddit context to tailor vocabulary and style.
- If the content is informational, lead with a hook question or surprising fact.
- If it's a discussion post, frame it to invite genuine responses.
- Avoid excessive emojis, clickbait, or overly promotional language.
- Structure: compelling title + well-formatted body (use markdown where appropriate).
- Keep paragraphs short — Reddit is read on mobile.

Respond with JSON:
{
  "title": "The post title",
  "body": "The post body in Reddit-flavored markdown"
}""",

    "reddit_comment": """You are a helpful Reddit community member.
Write authentic, relevant comments. Be concise, add value, and match the
subreddit's tone. Never be self-promotional unless the context is appropriate.

Respond with JSON:
{
  "body": "The comment text"
}""",

    "refine": """You are a writing editor. The user will give you a Reddit post draft
and feedback. Improve the draft based on the feedback while preserving the
author's voice. Return the same JSON format:
{
  "title": "Revised title",
  "body": "Revised body"
}""",
}


def get_azure_client() -> AzureOpenAI:
    """Create and return an Azure OpenAI client from env vars."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


def generate_content(
    idea: str,
    target_subreddits: list[str],
    content_type: str = "reddit_post",
    extra_context: str = "",
) -> dict:
    """
    Send an idea to Azure OpenAI and return structured content.

    Returns: {"title": "...", "body": "..."} or {"body": "..."}
    """
    client = get_azure_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

    system_prompt = SYSTEM_PROMPTS.get(content_type, SYSTEM_PROMPTS["reddit_post"])

    subreddit_context = ", ".join(f"r/{s}" for s in target_subreddits) if target_subreddits else "general"

    user_message = f"""Target subreddit(s): {subreddit_context}
{f'Additional context: {extra_context}' if extra_context else ''}

Idea/Draft:
{idea}"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_completion_tokens=2000,
        response_format={"type": "json_object"},
    )

    import json
    content = response.choices[0].message.content
    return json.loads(content)


def refine_content(current_title: str, current_body: str, feedback: str) -> dict:
    """Refine an existing draft based on user feedback."""
    client = get_azure_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

    user_message = f"""Current draft:
Title: {current_title}
Body: {current_body}

Feedback / requested changes:
{feedback}"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPTS["refine"]},
            {"role": "user", "content": user_message},
        ],
        max_completion_tokens=2000,
        response_format={"type": "json_object"},
    )

    import json
    return json.loads(response.choices[0].message.content)


def test_connection() -> dict:
    """Quick connectivity test to Azure OpenAI."""
    try:
        client = get_azure_client()
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "Respond with a single word: 'connected'"},
                {"role": "user", "content": "Test"},
            ],
            max_completion_tokens=10,
        )
        return {"status": "ok", "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "error": str(e)}
