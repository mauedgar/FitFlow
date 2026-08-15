from rag.configs.config import init_settings
from rag.scripts.indexer import get_or_create_index


def main():
    # 1. Inicializar modelos locales
    init_settings()
    # 2. Obtener o indexar la fuente de verdad
    index = get_or_create_index()

    # 3. Crear el motor de consultas
    query_engine = index.as_query_engine(similarity_top_k=3)

    # 4. Ejecutar consulta de prueba
    query = "¿Cuál es el procedimiento estándar según la documentación?"
    print(f"\nPregunta: {query}")

    response = query_engine.query(query)
    print(f"\nRespuesta de Gemma:\n{response}")

if __name__ == "__main__":
    main()
