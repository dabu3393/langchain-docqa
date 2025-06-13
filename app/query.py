from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from utils.load_env import load_env
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Initialize console
console = Console()

# Load environment variables
load_env()

# Load vector store
vectordb = Chroma(persist_directory="vector_store", embedding_function=OpenAIEmbeddings())

# Print total documents in vector store
console.print(f"\n📦 Total documents in vector store: {vectordb._collection.count()}")  # Internal but still works

# Set up the retriever
def get_docs_with_scores(query, k=4):
    return vectordb.similarity_search_with_score(query, k=k)

# Custom prompt template
template = """You are an expert assistant answering questions using only the context below. 
If the answer is not contained in the context, say: "I don't know based on the document."

Context:
{context}

Question:
{question}

Answer:"""

prompt = PromptTemplate.from_template(template)

# Set up the LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Test the chain
while True:
    user_input = input("\nAsk a question about your document (or type 'exit'): ").strip()
    if user_input.lower() == "exit":
        break
        
    docs_and_scores = get_docs_with_scores(user_input)
    docs = [doc for doc, score in docs_and_scores]
    context = "\n\n".join([doc.page_content for doc in docs])

    formatted_prompt = prompt.format(context=context, question=user_input)
    response = llm.invoke([HumanMessage(content=formatted_prompt)])

    console.print(Panel.fit(Markdown(f"### Answer:\n{response.content}"), title="Answer", style="cyan"))

    console.print("\n[bold green]Source Snippets with Scores:[/bold green]")
    for i, (doc, score) in enumerate(docs_and_scores):
        snippet = doc.page_content.strip().replace("\n", " ")[:200]

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

        console.print(f"[{i+1}] (Score: {score_text}) {snippet}...\n")

