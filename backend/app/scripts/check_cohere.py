"""
Verificación rápida: confirma que el SDK de Cohere está instalado,
que PydanticAI puede importar CohereModel, y que tu API key funciona
contra el modelo real.

Uso:
    python -m app.scripts.check_cohere
"""

import asyncio


def check_imports() -> bool:
    try:
        import cohere  # noqa: F401
        print(f"✅ cohere SDK instalado — versión {cohere.__version__}")
    except ImportError as exc:
        print(f"❌ cohere SDK NO instalado: {exc}")
        print('   Corre: uv add "pydantic-ai-slim[cohere]"')
        return False

    try:
        from pydantic_ai.models.cohere import CohereModel  # noqa: F401
        from pydantic_ai.providers.cohere import CohereProvider  # noqa: F401
        print("✅ pydantic_ai.models.cohere importa correctamente")
    except ImportError as exc:
        print(f"❌ PydanticAI no puede importar CohereModel: {exc}")
        return False

    return True


async def check_live_call() -> None:
    from app.config import get_settings
    from pydantic_ai import Agent
    from pydantic_ai.models.cohere import CohereModel
    from pydantic_ai.providers.cohere import CohereProvider

    settings = get_settings()
    if settings.cohere_api_key is None:
        print("⚠️  settings.cohere_api_key es None — revisa tu .env (COHERE_API_KEY)")
        return

    model = CohereModel(
        "command-a-03-2025",
        provider=CohereProvider(api_key=settings.cohere_api_key.get_secret_value()),
    )
    agent = Agent(model)

    try:
        result = await agent.run("Responde únicamente con la palabra: OK")
        print(f"✅ Llamada real a Cohere exitosa. Respuesta: {result.output!r}")
    except Exception as exc:
        print(f"❌ La llamada real a Cohere falló: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    if check_imports():
        asyncio.run(check_live_call())
