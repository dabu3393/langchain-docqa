from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils.load_env import load_env

# Load API key
load_env()

# Set up LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Send a message
response = llm.invoke([
    HumanMessage(content="What's a large language model?")
])

print("Response:\n", response.content)
