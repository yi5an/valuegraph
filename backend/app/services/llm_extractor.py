"""
LLM 实体和关系抽取服务 - 使用 LLM（GLM-5-Turbo / Ollama fallback）
"""
import httpx
import json
import logging
import re
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class LLMExtractor:
    """用 LLM API 做实体和关系抽取"""

    TIMEOUT = 15.0

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
        self.llm_base = getattr(settings, 'llm_api_base', '') or ''
        self.llm_key = getattr(settings, 'llm_api_key', '') or ''
        self.llm_model = getattr(settings, 'llm_model', '') or ''
        self.use_ollama = not (self.llm_base and self.llm_key and self.llm_model)
        if self.use_ollama:
            logger.info("实体抽取: 使用 Ollama (本地)")
        else:
            logger.info(f"实体抽取: 使用 {self.llm_model}")

    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用 Ollama API"""
        try:
            response = await self.client.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.TimeoutException:
            logger.warning("Ollama API 超时")
            return None
        except Exception as e:
            logger.error(f"调用 Ollama 失败: {e}")
            return None

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """调用 OpenAI 兼容 LLM API"""
        try:
            response = await self.client.post(
                f"{self.llm_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.llm_key}"},
                json={
                    "model": self.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                }
            )
            response.raise_for_status()
            data = response.json()
            msg = data["choices"][0]["message"]
            return msg.get("content") or msg.get("reasoning_content") or ""
        except httpx.TimeoutException:
            logger.warning(f"{self.llm_model} API 超时")
            return None
        except Exception as e:
            logger.error(f"调用 {self.llm_model} 失败: {e}")
            return None

    async def _call_model(self, prompt: str) -> Optional[str]:
        if not self.use_ollama:
            result = await self._call_llm(prompt)
            if result:
                return result
            logger.warning(f"{self.llm_model} 失败，fallback 到 Ollama")
        return await self._call_ollama(prompt)

    def _parse_json_from_text(self, text: str) -> Optional[Dict]:
        try:
            return json.loads(text)
        except:
            pass
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        brace_pattern = r'\{[^{}]*\}'
        match = re.search(brace_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return None

    async def extract_entities_and_relations(self, text: str, stock_code: str = None) -> Dict[str, Any]:
        """从文本中抽取实体和关系"""
        prompt = f"""从以下财经新闻中提取实体和关系。

新闻内容：
{text[:500]}

请返回 JSON 格式：
{{
  "entities": [
    {{"name": "实体名称", "type": "company/stock/government/person", "stock_code": "股票代码（如有）"}}
  ],
  "relations": [
    {{"from": "实体A", "to": "实体B", "type": "invests_in/competes_with/supplies_to/partner_of/REGULATED_BY"}}
  ]
}}

只返回 JSON，不要其他内容。"""

        response_text = await self._call_model(prompt)

        default_result = {"entities": [], "relations": []}

        if not response_text:
            return default_result

        result = self._parse_json_from_text(response_text)
        if not result:
            return default_result

        if 'entities' not in result:
            result['entities'] = []
        if 'relations' not in result:
            result['relations'] = []

        return result
