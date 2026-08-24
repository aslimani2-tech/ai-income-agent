import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY was not found in .env")

client = Groq(api_key=api_key)


def save_report(filename, content):
    """Save a report inside the reports folder."""

    os.makedirs("reports", exist_ok=True)

    filename = os.path.basename(filename)

    if not filename.endswith(".txt"):
        filename += ".txt"

    path = os.path.join("reports", filename)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Report saved successfully: {path}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "save_report",
            "description": (
                "Save a completed research report as a text file "
                "inside the reports folder."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename for the report."
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete report content."
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "browser_search"
    }
]


SYSTEM_PROMPT = """
You are the AI Income Research Agent.

Your job is to help the user discover realistic and legal
business opportunities using AI.

You can:
1. Search the web when current information is required.
2. Analyze information you find.
3. Save completed reports using the save_report tool.

When the user asks for current research, use browser_search.

When the user explicitly asks for a report to be saved,
use save_report.

Do not invent facts, companies, prices, websites, or sources.
Clearly distinguish verified information from your own analysis.

Your goal is to produce useful research that could eventually
help the user find clients and generate additional income.
"""


def run_agent(task):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": task
        }
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    # Display tool activity
    if message.tool_calls:
        print("\n🛠️ TOOLS USED:")

        for tool_call in message.tool_calls:
            print(f"   • {tool_call.function.name}")

    # If the model requested save_report, execute it.
    if message.tool_calls:

        messages.append(message)

        for tool_call in message.tool_calls:

            if tool_call.function.name == "save_report":

                arguments = json.loads(
                    tool_call.function.arguments
                )

                result = save_report(
                    arguments["filename"],
                    arguments["content"]
                )

                print(f"\n📄 {result}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    }
                )

        # Ask the model for the final response.
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools,
        )

        return final_response.choices[0].message.content

    return message.content


if __name__ == "__main__":

    print("=" * 60)
    print("🤖 AI INCOME RESEARCH AGENT v2")
    print("=" * 60)

    task = input("\nWhat should the agent research?\n> ")

    try:

        answer = run_agent(task)

        print("\n🤖 FINAL RESULT")
        print("-" * 60)
        print(answer)

    except Exception as error:

        print("\n❌ ERROR")
        print("-" * 60)
        print(error)