import os
import re
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

    if not filename.lower().endswith(".txt"):
        filename += ".txt"

    path = os.path.join("reports", filename)

    with open(path, "w", encoding="utf-8-sig") as file:
        file.write(content)

    return path


SYSTEM_PROMPT = """
You are the AI Income Research Agent.

Your job is to perform practical business research using
publicly available information and produce useful client-ready reports.

RESEARCH RULES:

1. When research is requested, use the available browser search.

2. Never invent facts, numbers, ratings, reviews, followers,
   traffic, analytics, technical measurements, prices, or business details.

3. Never invent or fabricate sources or URLs.

4. Only cite information actually obtained during the current research.

5. Never claim that something does not exist merely because it
   was not found during a web search.

6. For negative findings such as:
   - no Google Business Profile
   - no analytics
   - no social-media account
   - no schema markup
   - no direct booking system

   write "Not publicly verified" unless the research provides
   direct evidence.

7. Clearly distinguish:
   - VERIFIED FACTS
   - OBSERVATIONS
   - ANALYSIS
   - RECOMMENDATIONS

8. Never present an inference or assumption as a verified fact.

REPORT RULES:

When creating a business audit:

- Keep it concise and professional.
- Make it useful to a real business owner.
- Do not fabricate private analytics.
- Do not claim that a technical feature was tested unless it was actually tested.
- Make recommendations specific to the business.
- Include a SOURCES section with the URLs actually used.

AI SERVICE RULES:

Only recommend services that a beginner could realistically
deliver using AI, public information, and simple business tools.

Do not recommend complex API integrations, custom software,
advanced analytics implementation, or other technical work
unless the report clearly labels it as requiring a developer.

IMPORTANT:

Python will save the final response automatically.
Do not claim that the report was saved.
Simply produce the complete final report.
"""


def extract_filename(task):
    """Extract the requested .txt filename."""

    matches = re.findall(
        r'[\w\-]+\.txt',
        task,
        flags=re.IGNORECASE
    )

    if matches:
        return matches[-1]

    return None


def detect_research_mode(task):
    """Determine whether the task requires current web research."""

    keywords = [
        "research",
        "search",
        "current",
        "latest",
        "audit",
        "digital presence",
        "online presence",
        "competitor",
        "market research",
        "find businesses",
        "find restaurants"
    ]

    task_lower = task.lower()

    return any(
        keyword in task_lower
        for keyword in keywords
    )


def run_agent(task, research_mode=False):

    prompt = SYSTEM_PROMPT + "\n\nUSER TASK:\n" + task

    tools = []

    if research_mode:
        tools = [
            {
                "type": "browser_search"
            }
        ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        tools=tools,
        tool_choice="required" if research_mode else "auto",
        reasoning_effort="low",
        include_reasoning=False,
        max_completion_tokens=1800,
        temperature=0.3,
    )

    message = response.choices[0].message

    if not message.content:
        raise RuntimeError(
            "The model returned an empty response."
        )

    return message.content


if __name__ == "__main__":

    print("=" * 60)
    print("AI INCOME RESEARCH AGENT V7")
    print("=" * 60)

    task = input("\nWhat should the agent do?\n> ")

    research_mode = detect_research_mode(task)

    print(
        "\nResearch mode:",
        "ON" if research_mode else "OFF"
    )

    try:

        answer = run_agent(
            task,
            research_mode=research_mode
        )

        print("\nFINAL RESULT")
        print("-" * 60)
        print(answer)

        filename = extract_filename(task)

        if filename:

            path = save_report(
                filename,
                answer
            )

            print(
                f"\nREPORT SAVED: {path}"
            )

        else:

            print(
                "\nREPORT NOT SAVED: "
                "No .txt filename was provided."
            )

    except Exception as error:

        print("\nERROR")
        print("-" * 60)
        print(error)