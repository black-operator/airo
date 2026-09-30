import json
import threading

import requests


generation_lock = threading.Lock()


class OllamaError(RuntimeError):
    pass


def status(base_url, model):
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=2.5)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = {item.get("name") for item in models}
        return {
            "online": True,
            "model_ready": model in names or f"{model}:latest" in names,
            "model": model,
        }
    except requests.RequestException:
        return {"online": False, "model_ready": False, "model": model}


def stream_chat(base_url, model, messages):
    acquired = generation_lock.acquire(timeout=120)
    if not acquired:
        raise OllamaError("Das Modell ist noch mit einer anderen Antwort beschäftigt.")
    response = None
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "keep_alive": "10m",
            },
            stream=True,
            timeout=(10, 600),
        )
        if response.status_code == 404:
            raise OllamaError(f"Das Ollama-Modell „{model}“ wurde noch nicht erstellt.")
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            packet = json.loads(line)
            if packet.get("error"):
                raise OllamaError(packet["error"])
            content = packet.get("message", {}).get("content", "")
            if content:
                yield content
            if packet.get("done"):
                break
    except requests.RequestException as exc:
        raise OllamaError("Ollama ist nicht erreichbar. Starte Ollama und versuche es erneut.") from exc
    finally:
        if response is not None:
            response.close()
        generation_lock.release()
