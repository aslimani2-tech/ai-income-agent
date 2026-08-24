import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY was not found in .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)


def save_report(filename, content):
    """Save a report inside the reports folder."""

    os.makedirs("reports", exist_ok=True)

    # Keep the filename safe
    filename = os.path.basename(filename)

    if not filename.endswith(".txt"):
        filename += ".txt"

    path = os.path.join("reports", filename)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Report saved successfully at: {path}"


# The tool definition that we give to the AI model
tools = [
    {
        "type": "function",
        "function": {
            "name": "save_report",
            "description": (
                "Save a completed report as a text file inside "
                "the reports folder."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename for the report."
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete report content."
                    }
                },
                "required": ["filename", "content"]
            }
        }
    }
]


def run_agent(task):

    messages = [
        {
            "role": "system",
            "content": (
                "You are the AI Income Agent. "
                "You help the user create practical, legal and "
                "realistic income opportunities using AI. "
                "You have access to a save_report tool. "
                "When the user explicitly asks you to create and "
                "save a report, use the save_report tool."
            )
        },
        {
            "role": "user",
            "content": task
        }
    ]

    # First request: ask the model what it wants to do
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    # If the model wants to use a tool
    if message.tool_calls:

        messages.append(message)

        for tool_call in message.tool_calls:

            if tool_call.function.name == "save_report":

                arguments = json.loads(tool_call.function.arguments)

                result = save_report(
                    arguments["filename"],
                    arguments["content"]
                )

                print("\n🛠️ TOOL USED: save_report")
                print(result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    }
                )

        # Send the tool result back to the AI
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools,
        )

        return final_response.choices[0].message.content

    # If no tool was needed
    return message.content


if __name__ == "__main__":

    print("=" * 55)
    print("🤖 AI INCOME AGENT — TOOL USE VERSION")
    print("=" * 55)

    task = input("\nWhat do you want the agent to do?\n> ")

    try:

        answer = run_agent(task)

        print("\n🤖 AGENT RESPONSE")
        print("-" * 55)
        print(answer)

    except Exception as error:

        print("\n❌ ERROR")
        print("-" * 55)
        print(error)