"""火山 ARK 对话客户端（OpenAI 兼容 chat completions）。"""
import httpx

from app.config import get_settings


async def chat_completion(system_prompt: str, user_prompt: str,
                          temperature: float = 0.3) -> str:
    s = get_settings()
    if not s.ark_api_key:
        raise RuntimeError("未配置 ARK_API_KEY")
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
        resp = await client.post(
            f"{s.ark_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {s.ark_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": s.ark_chat_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


async def vision_extract(data_url: str, instruction: str,
                         temperature: float = 0.0) -> str:
    """多模态抽取：传入 data:image/...;base64 URL，返回模型文本。"""
    s = get_settings()
    if not s.ark_api_key:
        raise RuntimeError("未配置 ARK_API_KEY")
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
        resp = await client.post(
            f"{s.ark_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {s.ark_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": s.ark_chat_model,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": instruction},
                    ]},
                ],
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]
