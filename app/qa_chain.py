# app/qa_chain.py
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.utils.load_env import load_env

load_env()

vectordb = Chroma(persist_directory="vector_store", embedding_function=OpenAIEmbeddings())
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

template = """You are an expert assistant answering questions using only the context below. 
If the answer is not contained in the context, say: "I don't know based on the document."

Context:
{context}

Question:
{question}

Answer:"""
prompt = PromptTemplate.from_template(template)

def get_docs_with_scores(query, k=4):
    return vectordb.similarity_search_with_score(query, k=k)

def answer_question(query: str, k: int = 4):
    docs_and_scores = get_docs_with_scores(query, k=k)
    docs = [doc for doc, _ in docs_and_scores]
    context = "\n\n".join([doc.page_content for doc in docs])
    formatted_prompt = prompt.format(context=context, question=query)
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    return {
        "answer": response.content,
        "sources": [
            {
                "source": doc.metadata.get("source", "Unknown"),
                "snippet": doc.page_content.strip().replace("\n", " ")[:200]
            }
            for doc, _ in docs_and_scores
        ]
    }
