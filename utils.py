import os
import re
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import VideoUnavailable, TranscriptsDisabled
from huggingface_hub import InferenceClient



# =========================
# GROQ CLIENT
# =========================
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# =========================
# HUGGING FACE CLIENT
# =========================
def get_hf_client():
    token = os.getenv("HF_TOKEN")
    if not token:
        return None

    return InferenceClient(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        token=token
    )


# =========================
# TEXT CHUNKING HELPER
# =========================
def chunk_text(text, max_chars=4000):
    """
    Split long text into smaller chunks to avoid hitting Groq token limits
    """
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + max_chars])
        start += max_chars
    return chunks

# =========================
# YOUTUBE VIDEO ID EXTRACTOR
# =========================
def extract_video_id(url):
    """
    Extracts YouTube video ID from full URL
    Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - Shorts
    """
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"shorts/([a-zA-Z0-9_-]{11})"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None



# =========================
# CHAT WITH LLM
# =========================
def chat_with_llm(messages):
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages[-6:]
    )
    return completion.choices[0].message.content


# =========================
# PDF SUMMARY
# =========================
def summarize_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = "".join(page.extract_text() or "" for page in reader.pages)

    chunks = chunk_text(text)
    partial_summaries = []

    # Summarize each chunk separately
    for chunk in chunks:
        prompt = f"Summarize this part of the PDF clearly:\n{chunk}"
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        partial_summaries.append(completion.choices[0].message.content)

    # Combine partial summaries into one final summary
    final_prompt = "Combine these into one clear summary:\n" + "\n".join(partial_summaries)
    final_completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": final_prompt}]
    )
    return final_completion.choices[0].message.content


# =========================
# YOUTUBE SUMMARY
# =========================
def summarize_youtube(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        return "Invalid YouTube URL"

    try:
        # Try English first, fallback to Telugu auto-generated
        try:
            transcript_data = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
        except:
            transcript_data = YouTubeTranscriptApi().fetch(video_id, languages=['te'])

        full_text = " ".join(item.text for item in transcript_data)

        chunks = chunk_text(full_text)
        partial_summaries = []

        # Summarize each chunk separately
        for chunk in chunks:
            prompt = f"Summarize this part of the YouTube transcript clearly:\n{chunk}"
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            partial_summaries.append(completion.choices[0].message.content)

        # Combine partial summaries into one final summary
        final_prompt = "Combine these into one clear summary:\n" + "\n".join(partial_summaries)
        final_completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": final_prompt}]
        )

        return final_completion.choices[0].message.content

    except VideoUnavailable:
        return "Transcript unavailable: video removed or private."
    except TranscriptsDisabled:
        return "Transcript unavailable: captions disabled."
    except Exception as e:
        return f"Error: {str(e)}"

# =========================
# IMAGE GENERATION
# =========================
def generate_image(prompt, output_path="generated_image.png"):
    hf_client = get_hf_client()

    if hf_client is None:
        return "❌ HF_TOKEN not detected. Restart Streamlit after adding it."

    image = hf_client.text_to_image(prompt)
    image.save(output_path)
    return output_path
