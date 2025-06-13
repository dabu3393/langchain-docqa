from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OpenAI API key not found")

# Set up LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Send a message
response = llm.invoke([
    HumanMessage(content="What's a large language model?")
])

print("Response:\n", response.content)
