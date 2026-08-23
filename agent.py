import os
from dotenv import load_dotenv
from openai import OpenAI

# Load our secret key from .env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY was not found. Check your .env file."
    )

# Connect the OpenAI Python library to Groq
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

def ask_agent(task):
    response = client.responses.create(
        model="openai/gpt-oss-20b",
        instructions=(
            "You are the AI Income Agent. "
            "Your job is to help the user find practical, "
            "legal and realistic ways to create additional income "
            "using AI and automation."
        ),
        input=task,
    )

    return response.output_text


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 AI INCOME AGENT")
    print("=" * 50)

    task = input("\nWhat do you want the agent to do?\n> ")

    try:
        answer = ask_agent(task)

        print("\n🤖 AGENT RESPONSE")
        print("-" * 50)
        print(answer)

    except Exception as error:
        print("\n❌ ERROR")
        print("-" * 50)
        print(error)