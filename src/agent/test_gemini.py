from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"


def main():

    print("\n" + "=" * 70)
    print("ORBIT.AI — GEMINI API CONNECTION TEST")
    print("=" * 70)

    load_dotenv(ENV_FILE)

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    if api_key.startswith("PASTE_"):
        raise ValueError(
            "GEMINI_API_KEY still contains "
            "the placeholder value."
        )

    print("\nAPI key detected: YES")
    print(f"Model: {model}")

    client = genai.Client(
        api_key=api_key
    )

    print("\nSending test request...")

    interaction = client.interactions.create(
        model=model,
        input=(
            "Reply with exactly: "
            "ORBIT.AI GEMINI CONNECTION SUCCESS"
        )
    )

    print("\nGemini response:")
    print(interaction.output_text)

    print("\n" + "=" * 70)
    print("GEMINI API CONNECTION TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()