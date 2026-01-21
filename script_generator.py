from groq import Groq
from google import genai 
from google.genai import types
from dotenv import load_dotenv
import json
import random
import os
from openai import OpenAI

load_dotenv()

# ------------------ Clients ------------------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
client = genai.Client(api_key=os.getenv("GENAI_API_KEY")) 


# ------------------ Constants ------------------
TOPIC_GENRES = [
    'Romance',
    'Relationships',
    'Dating Advice',
    'Psychology',
    'AI',
    'Sex Education',
    'Love',
    'Intimacy',
    'Fun Facts',
    'Sex',
    'Adulting',
    'Romantic Comedy',
    'Flirting Tips',
    'Relationship Psychology',
    'Hookup Culture',
    'Love Languages',
    'Breakup Advice',
    'Long Distance Relationships',
    'Dating Apps',
    'Modern Dating',
    'Self-Love',
    'Attraction Science',
    'Seduction Tips',
    'Bedroom Tips',
    'Erotic Stories',
    'Fantasies & Desires',
    'Kinks & Fetishes',
    'Consent & Boundaries',
    'Polyamory & Open Relationships',
    'Cheating & Infidelity',
    'Jealousy & Trust Issues',
    'Passion & Romance Hacks',
    'Relationship Red Flags',
    'Flirting Psychology',
    'Sexual Health',
    'Orgasm Tips',
    'Couple Goals',
    'Spicy Challenges',
    'Sexy Fun Facts',
    'Adult Humor',
    'Romantic Surprises',
    'Dating Horror Stories',
    'Love & Emotions',
    'Hookup Stories',
    'Bedroom Chemistry',
    'Sexual Confidence',
    'Intimate Communication',
    'Body Positivity & Sexuality',
    'Modern Love Trends',
    'Dating Etiquette',
    'Sensual Wellness',
    'Dating Experiments',
    'Crush Advice',
    'Passionate Romance',
    'Love Memes',
    'Digital Threesomes',
    'AI Sex & Erotic AI',
    'Playful Pleasure',
    'Office Sex Revival',
    'IRL Hookups',
    'Age-Gap Heat',
    'Pegging Power',
    'Femdom Rules',
    'Chastity Games',
    'Cuckold Fantasies',
    'Praise Kink',
    'Humiliation Play',
    'Audio Erotica',
    'Self-Pleasure Era'
    'Edging & Orgasm Control',
    'Sexting Foreplay',
    'Modern Monogamy',
    'Wax & Ice Play',
    'Sex Fights',
    'Spicy Couple Challenges',
    'Sexual Confidence',
    'Intimate Dirty Talk',
    'Kink Exploration',
    'Digital Foreplay',
    'Fetish Fun',
    'Intimate Communication Mastery'
]


OPENROUTER_MODELS = [
    "google/gemma-3n-e4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/devstral-2512:free",
    "xiaomi/mimo-v2-flash:free",
    "nvidia/nemotron-3-nano-30b-a3b:free"
]

# ------------------ Helpers ------------------
def clean_json(text: str) -> str:
    """Remove markdown fences and whitespace"""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
        text = text.replace("json", "", 1).strip()
    return text

def extract_json_safe(text: str) -> dict:
    """Extract valid JSON from text, raise if invalid"""
    try:
        cleaned = clean_json(text)
        return json.loads(cleaned)
    except Exception:
        # fallback regex for safety
        import re
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No valid JSON found in model output")
        return json.loads(match.group())

# ------------------ Provider Implementations ------------------
def generate_openrouter(prompt: str) -> dict:
    """Try multiple free models on OpenRouter until one works"""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY")
    )
    
    last_exception = None
    for model in OPENROUTER_MODELS:
        try:
            response = client.responses.create(
                model=model,
                input=prompt,
            )
            text = response.output[0].content[0].text
            return extract_json_safe(text)
        except Exception as e:
            last_exception = e
            print(f"OpenRouter model {model} failed: {e}")
    raise RuntimeError(f"All OpenRouter models failed: {last_exception}")

def generate_gemini(prompt: str) -> dict:
    """
    Gemini provider with multi-model fallback.
    Tries several free/preview models in order until one succeeds.
    """
    # List of Gemini free or preview models
    models = [
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash-preview-09-2025",
        "gemini-2.5-flash-lite-preview-09-2025"
    ]
    
    last_exception = None
    
    for model in models:
        try:
            print(f"Trying Gemini model {model}...")
            response = gemini_client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            last_exception = e
            print(f"Gemini model {model} failed → {e}")
    
    raise RuntimeError(f"All Gemini models failed: {last_exception}")


def generate_groq_llama(prompt: str) -> dict:
    """Groq Free Tier generation"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Groq failed: {e}")

# ------------------ Fallback Mechanism ------------------
def generate_with_fallback(prompt: str) -> dict:
    """Try multiple providers until one returns valid JSON"""
    providers = [generate_gemini,generate_groq_llama,generate_openrouter]
    last_exception = None
    for provider in providers:
        try:
            print(f"Trying {provider.__name__}...")
            result = provider(prompt)
            if result and isinstance(result, dict):
                return result
        except Exception as e:
            last_exception = e
            print(f"{provider.__name__} failed → {e}")
    raise RuntimeError(f"All AI providers failed: {last_exception}")

# ------------------ Core Prompt ------------------
def build_youtube_short_prompt(genre: str) -> str:
    return f"""
You are an expert viral YouTube Shorts creator specializing in {genre} content.

Create a complete YouTube Short content package based on the topic: "{genre}"

CORE GOAL:
Make viewers click because of the TITLE and keep watching because the video feels like a LOOP.

REQUIREMENTS:

TITLE:
- Very short (5–10 words)
- Extremely curiosity-driven
- Creates a strong "wait, what?" reaction
- Avoid generic words
- No emojis, no hashtags

SCRIPT:
- Spoken, natural, conversational tone
- 50–60 seconds long
- FIRST LINE must be almost identical to the LAST LINE
- The first line should introduce a bold or intriguing statement
- No symbols or text that text-to-speech can't recognize
- Flowlessly spoken by text-to-speech
- The script must END with either: "that's why..." OR "so..." OR "and this is why..."
- When the video restarts, the ending should smoothly connect back to the beginning, creating a seamless loop

DESCRIPTION:
- 2–3 short lines
- Builds curiosity without giving away the answer
- Encourages viewers to watch till the end

HASHTAGS:
- 5–10 relevant and trending hashtags
- Related to curiosity, knowledge, facts, psychology, or learning

OUTPUT FORMAT:
Return ONLY valid JSON in the exact format below.
Do not include explanations, markdown, or extra text.

{{
    "title": "",
    "script": "",
    "description": "",
    "tags": []
}}
"""

# ------------------ Public Function ------------------
def generate_youtube_short_metadata(genre: str) -> dict:
    prompt = build_youtube_short_prompt(genre)
    try:
        return generate_with_fallback(prompt)
    except Exception as e:
        print(f"All providers failed: {e}")
        return None
    
def chunks_to_pexels_titles(chunks: list[str]) -> list[dict]:
    full_text = ' '.join(chunks)
    prompt = f"""
    You are generating stock video search titles for Pixabay.
    Rules:
    - One title per chunk
    - Titles must be 3–7 words
    - Use generic, visual, stock-video-friendly concepts
    - Avoid abstract language that has no visuals
    - Focus on broad themes (brain, science, technology, psychology, people, abstract visuals)
    - Do NOT repeat the chunk text
    - Do NOT explain anything
    - Output VALID JSON ONLY
    - Likely to exist as a stock video
    Requirements:
    - Title: "From above rule result".

    Input chunks:
    {json.dumps(chunks, ensure_ascii=False)}

    For each chunk in chunks generate a title based on given rule also the genbearted title should be base don the core theme or concpet of {full_text} and should be in categories of 
    Curiosity & Knowledge

    Return the output in this JSON format:
    {{
        "title":['title1','title2'],
        
    }}
    """
    # print(prompt)
    try:
        return generate_with_fallback(prompt)
    except Exception as e:
        print(f"All providers failed: {e}")
        return None


# ------------------ Example Usage ------------------
def get_genre() -> str:
    return random.choice(TOPIC_GENRES)



