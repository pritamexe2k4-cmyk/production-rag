from langchain.agents import create_agent
from langchain_ollama import ChatOllama



model = ChatOllama(
    model="qwen3:4b",
    base_url="http://localhost:11434"
)

agent = create_agent(
    model=model,
    system_prompt="You are physics and biology expert, You have to answer the question of the user in a fun and interactive format ",
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "how is the physics related to biology in the most fun format"}]}
)

print(response["messages"][-1].content)