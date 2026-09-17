import httpx

from app.core.config import settings

class BaseAgent:
    def __init__(self, model_name: str | None = None, base_url: str | None = None):
        raw_url = base_url or settings.ollama_base_url

        self.base_url = f"{raw_url.rstrip('/')}/api/chat"
        self.model_name = model_name or settings.ollama_model

    # Send a chat request to the LLM backend (Ollama) and return the response content string
    async def chat(
            self,
            messages: list[dict],
            format: str | None = 'json',
            timeout: float = 90.0
    ) -> str:
        payload = {
            'model': self.model_name,
            'messages': messages,
            'stream': False
        }

        if format:
            payload['format'] = format

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f'LLM backend returned status {response.status_code}: {response.text}'
                )

            data = response.json()

            # Ollama wraps its answer inside {"message": {"role": "assistant", "content": "{ ... }"}}.

            return data['message']['content']
