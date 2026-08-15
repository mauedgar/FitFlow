from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.lmstudio import LMStudio


def init_settings():
    # Configuración de Gemma en LM Studio
    Settings.llm = LMStudio(
        model_name="text-embedding-embeddinggemma-300m",
        base_url="http://localhost:1234/v1",
        temperature=0.2, # Un valor bajo es mejor para responder usando fuentes de verdad
        request_timeout=120.0,
    )

    # Configuración del modelo de Embeddings en LM Studio
    Settings.embed_model = OpenAIEmbedding(
        model="nomic-ai/nomic-embed-text-v1.5-GGUF",
        api_base="http://localhost:1234/v1",
        api_key="lm-studio",
    )
