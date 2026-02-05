import os
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condi
from tools import retriever_tool



os.environ["GOOGLE_API_KEY"] = "AIzaSyBvC4NDd7oHXPFEAXax-t4M17XCKoxoexk"

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=1.0,  # Gemini 3.0+ defaults to 1.0
    max_tokens=None,
    timeout=None,
    max_retries=2
)

template = """

You are a patent search and retrieval assistant.

Use the following pieces of retrieved context to answer the question.

If you don't know the answer, just say that you don't know.

Use three sentences maximum and keep the answer concise.

Here is relevant context: {context}

Here is the question: {question}

"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n")
    if question == "q":
        break
    
    context = retriever_tool.invoke(question)
    result = chain.invoke({"context": context, "question": question})
    print(result)