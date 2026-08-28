import sys
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

def interactive_chat():
    print("Loading vector store...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    print("Initializing LLM and conversation memory...")
    llm = Ollama(model="phi3")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    prompt_template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
You must always answer in English. Do not use any other language.

{context}

Question: {question}
Helpful Answer (in English):"""
    
    QA_PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT}
    )
    
    print("\nSystem ready. Type 'quit' or 'exit' to end the conversation.\n")
    
    while True:
        try:
            question = input("User: ")
            if question.strip().lower() in ["quit", "exit"]:
                print("Ending conversation.")
                break
            if not question.strip():
                continue
                
            result = qa_chain.invoke({"question": question})
            print(f"Assistant: {result['answer']}\n")
        except KeyboardInterrupt:
            print("\nEnding conversation.")
            break

if __name__ == "__main__":
    interactive_chat()
