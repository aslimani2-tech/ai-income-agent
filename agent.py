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
    """Save a report safely inside the reports folder."""

    os.makedirs("reports", exist_ok=True)

    filename = os.path.basename(filename)

    if not filename.endswith(".txt"):
        filename += ".txt"

    path = os.path.join("reports", filename)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Report saved successfully: {path}"


save_report_tool = {
    "type": "function",
    "function": {
        "name": "save_report",
        "description": (
            "Save a completed research report as a text file. "
            "Use this only when the user explicitly asks for the "
            "research to be saved."
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
            "required": ["filename", "content"],
            "additionalProperties": False
        }
    }
}


SYSTEM_PROMPT = """
You are the AI Income Research Agent.

Your job is to perform practical business research that can help
the user discover legitimate opportunities and potential clients.

Rules:

- Be concise and factual.
- Use web search when the user asks for current information,
  research, businesses, competitors, prices, or market information.
- Do not invent facts.
- Clearly distinguish facts from your analysis.
- When sources are available, preserve useful source references.
- Only save a report when the user explicitly asks you to save it.
- Keep reports practical and useful for business decisions.
"""


def run_agent(task, research_mode=False):

    messages = [
        {
            "role": "user",
            "content": SYSTEM_PROMPT + "\n\nUSER TASK:\n" + task
        }
    ]

    tools = [save_report_tool]

    # Add browser search only when research is actually requested.
    if research_mode:
        tools.append({
            "type": "browser_search"
        })

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        reasoning_effort="low",
        include_reasoning=False,
        max_completion_tokens=1500,
        temperature=0.4,
    )

    message = response.choices[0].message

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

                print("\n📄 " + result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        # One final call after the local tool execution.
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            reasoning_effort="low",
            include_reasoning=False,
            max_completion_tokens=500,
            temperature=0.4,
        )

        return final_response.choices[0].message.content

    return message.content


if __name__ == "__main__":

    print("=" * 60)
    print("🤖 AI INCOME RESEARCH AGENT v3")
    print("=" * 60)

    task = input("\nWhat should the agent do?\n> ")

    # Research mode is activated only for research/current-information tasks.
    research_keywords = [
        "research",
        "search",
        "current",
        "latest",
        "find businesses",
        "find restaurants",
        "competitors",
        "market",
        "audit"
    ]

    research_mode = any(
        keyword in task.lower()
        for keyword in research_keywords
    )

    print(
        "\n🔎 Research mode:",
        "ON" if research_mode else "OFF"
    )

    try:

        answer = run_agent(
            task,
            research_mode=research_mode
        )

        print("\n🤖 FINAL RESULT")
        print("-" * 60)
        print(answer)

    except Exception as error:

        print("\n❌ ERROR")
        print("-" * 60)
        print(error)