"""Question answering chain implementation using LangChain."""

import os

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import traceable

from app.utils.load_env import load_env

load_env()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    streaming=False,
    verbose=True,
)

"""Question answering template."""
TEMPLATE = """You are an expert assistant answering questions using only the context below.
If the answer is not contained in the context, say: "I don't know based on the document."

Context:
{context}

Question:
{question}

Answer:"""
prompt = PromptTemplate.from_template(TEMPLATE)

vectordb = Chroma(
    persist_directory="vector_store", embedding_function=OpenAIEmbeddings()
)


@traceable(name="Document Retrieval")
def get_docs_with_scores(query, k=4):
    """Retrieve documents and their relevance scores for a given query."""
    return vectordb.similarity_search_with_score(query, k=k)


@traceable(name="LLM Call")
def answer_question(query: str, k: int = 4):
    """Generate an answer to a question based on relevant documents."""
    docs_and_scores = get_docs_with_scores(query, k=k)
    docs = [doc for doc, _ in docs_and_scores]
    context = "\n\n".join([doc.page_content for doc in docs])
    formatted_prompt = prompt.format(context=context, question=query)
    response = llm.invoke([HumanMessage(content=formatted_prompt)])

    if not docs:
        return {"answer": "I don't know based on the document.", "sources": []}
    return {
        "answer": response.content,
        "sources": [
            {
                "source": os.path.basename(doc.metadata.get("source", "Unknown")),
                "snippet": doc.page_content.strip().replace("\n", " ")[:200],
                "score": round(score, 2) if score is not None else None,
            }
            for doc, score in docs_and_scores
        ],
    }
