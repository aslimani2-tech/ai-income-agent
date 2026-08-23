from datetime import datetime


def agent(task):
    print("\n🤖 AI Income Agent")
    print("-" * 40)
    print(f"Task received: {task}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAgent status: READY")
    print("Next step: connect an AI model and tools.")


if __name__ == "__main__":
    task = input("What should the agent do? ")
    agent(task)