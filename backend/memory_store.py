import os
import json

MEMORY_DIR = "./memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

def store_memory(doc_id: str, content: str):
    with open(os.path.join(MEMORY_DIR, f"{doc_id}.txt"), "w") as f:
        f.write(content)

def get_memory(doc_id: str):
    path = os.path.join(MEMORY_DIR, f"{doc_id}.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""