from app.qa_chain import answer_question
from utils.load_env import load_env
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import argparse

parser = argparse.ArgumentParser(description="Ask questions about ingested documents.")
parser.add_argument("--question", type=str, help="Question to ask the document.")
parser.add_argument("--k", type=int, default=4, help="Number of top results to return.")
args = parser.parse_args()

console = Console()

def ask_question(user_input):
    answer, docs_and_scores = answer_question(user_input, k=args.k)

    console.print(Panel.fit(Markdown(f"### Answer:\n{answer}"), title="Answer", style="cyan"))

    console.print("\n[bold green]Source Snippets with Scores:[/bold green]")
    for i, (doc, score) in enumerate(docs_and_scores):
        snippet = doc.page_content.strip().replace("\n", " ")[:200]
        filename = doc.metadata.get("source", "Unknown")

        if score is not None:
            # Color code score
            if score <= 0.3:
                score_color = "green"
            elif score <= 0.5:
                score_color = "yellow"
            else:
                score_color = "red"
            score_text = f"[{score_color}]{score:.2f}[/]"
        else:
            score_text = "[grey58]N/A[/]"

        console.print(f"[{i+1}] (Score: {score_text}) [bold blue]{filename}[/bold blue] - {snippet}...\n")


if args.question:
    ask_question(args.question)
else:
    while True:
        user_input = input("\nAsk a question about your document (or type 'exit'): ").strip()
        if user_input.lower() == "exit":
            break
        ask_question(user_input)
