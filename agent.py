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
    """Save the final report inside the reports folder."""

    os.makedirs("reports", exist_ok=True)

    filename = os.path.basename(filename)

    if not filename.lower().endswith(".txt"):
        filename += ".txt"

    path = os.path.join("reports", filename)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return path


SYSTEM_PROMPT = """
You are the AI Income Research Agent.

Your purpose is to create practical business research that can
help identify legitimate opportunities and potential clients.

RESEARCH RULES:

1. When web research is requested, use the available browser search.

2. Never invent facts, numbers, ratings, reviews, followers,
   traffic, analytics, technical measurements, prices, or business details.

3. Never claim that something does not exist merely because it
   was not found during a web search.

4. For negative findings such as "no Google Business Profile",
   "no analytics", "no social-media account", "no schema markup",
   or "no direct booking system", write "Not publicly verified"
   unless the current research provides direct evidence.

5. Distinguish clearly between:
   - VERIFIED FACT
   - OBSERVATION
   - ANALYSIS
   - RECOMMENDATION

6. Never present an inference or assumption as a verified fact.

REPORT RULES:

When creating a business audit:

- Keep it concise and client-ready.
- Focus on useful business findings.
- Use the following structure when appropriate:

1. VERIFIED FACTS
2. DIGITAL PRESENCE ANALYSIS
3. WEAKNESSES AND MISSED OPPORTUNITIES
4. AI SERVICES WE COULD OFFER
5. RECOMMENDED ACTION PLAN
6. SOURCES

- Make recommendations specific to the business being researched.
- Do not claim that something was technically tested unless it was
  actually tested.
- Do not claim access to private analytics or private business data.

IMPORTANT:

Python will save the final response automatically.
Do not claim that Python saved the report.
Simply produce the complete final report.
"""


def extract_filename(task):
    """
    Find a .txt filename inside the user's task.
    """

    matches = re.findall(
        r'[\w\-]+\.txt',
        task,
        flags=re.IGNORECASE
    )

    if matches:
        return matches[-1]

    return None


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
        tool_choice="required" if research_mode else "none",
        reasoning_effort="low",
        include_reasoning=False,
        max_completion_tokens=1800,
        temperature=0.3,
    )

    return response.choices[0].message.content


def detect_research_mode(task):

    keywords = [
        "research",
        "search",
        "current",
        "latest",
        "find businesses",
        "find restaurants",
        "competitors",
        "market",
        "audit",
        "digital presence",
        "online presence"
    ]

    task_lower = task.lower()

    return any(
        keyword in task_lower
        for keyword in keywords
    )


if __name__ == "__main__":

    print("=" * 60)
    print("AI INCOME RESEARCH AGENT V5")
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

        if filename and answer:

            path = save_report(
                filename,
                answer
            )

            print(
                f"\nREPORT SAVED: {path}"
            )

    except Exception as error:

        print("\nERROR")
        print("-" * 60)
        print(error)