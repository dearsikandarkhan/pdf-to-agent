from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from vector_store import get_top_k

llm = ChatOpenAI(temperature=0.3)
embedding_model = OpenAIEmbeddings()

def get_answer(doc_id: str, question: str, chat_history):
    query_embedding = embedding_model.embed_query(question)
    top_chunks = get_top_k(doc_id, query_embedding)

    context = "\n---\n".join(top_chunks)
    prompt = f"You are an assistant with access to the following document excerpts:\n{context}\n\nAnswer the user's question: {question}"

    if chat_history:
        prompt = f"Previous conversation:\n{chat_history}\n\n{prompt}"

    answer = llm.predict(prompt)
    updated_history = f"{chat_history}\nUser: {question}\nAI: {answer}" if chat_history else f"User: {question}\nAI: {answer}"

    return answer, updated_history