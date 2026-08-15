import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage

DATA_DIR = "./docs/*.md"
PERSIST_DIR = "./.context/storage/docs(L1)_vector_store"

def get_or_create_index():
    # Comprobar si ya existen embeddings procesados
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        print("-> Cargando embeddings existentes desde el almacenamiento local...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    else:
        print("-> No se encontraron embeddings. Procesando fuente de verdad...")
        # Cargar los documentos de la fuente de verdad
        documents = SimpleDirectoryReader(DATA_DIR).load_data()

        # Crear el índice (esto llamará a LM Studio para generar los vectores)
        index = VectorStoreIndex.from_documents(documents)

        # Guardar en el disco para la próxima vez
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        print(f"-> Embeddings guardados con éxito en: {PERSIST_DIR}")

    return index
