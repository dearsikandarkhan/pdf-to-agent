import faiss
import os
import pickle

VECTOR_STORE_DIR = "./vector_store"

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

vector_index = {}  # in-memory mapping: doc_id -> index object

def store_chunks(doc_id, chunks, embedded_chunks):
    dim = len(embedded_chunks[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embedded_chunks).astype('float32'))

    vector_index[doc_id] = (index, chunks)

    with open(os.path.join(VECTOR_STORE_DIR, f"{doc_id}.pkl"), "wb"):
        pickle.dump((index, chunks), f)

def get_top_k(doc_id, query_embedding, k=3):
    if doc_id not in vector_index:
        with open(os.path.join(VECTOR_STORE_DIR, f"{doc_id}.pkl"), "rb") as f:
            vector_index[doc_id] = pickle.load(f)

    index, chunks = vector_index[doc_id]
    D, I = index.search(query_embedding.reshape(1, -1), k)
    return [chunks[i] for i in I[0]]
