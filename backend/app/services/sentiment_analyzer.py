"""
情感分析服务 - 使用 LLM（GLM-5-Turbo / Ollama fallback）
"""
import httpx
import json
import logging
import re
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情感分析器"""

    TIMEOUT = 15.0

    def __init__(self):
        """初始化情感分析器"""
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
        # 优先使用配置的 LLM API（如 GLM-5-Turbo），否则 fallback 到 Ollama
        self.llm_base = getattr(settings, 'llm_api_base', '') or ''
        self.llm_key = getattr(settings, 'llm_api_key', '') or ''
        self.llm_model = getattr(settings, 'llm_model', '') or ''
        self.use_ollama = not (self.llm_base and self.llm_key and self.llm_model)
        if self.use_ollama:
            logger.info("情感分析: 使用 Ollama (本地)")
        else:
            logger.info(f"情感分析: 使用 {self.llm_model}")

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
        """调用 OpenAI 兼容 LLM API（GLM-5-Turbo 等）"""
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
            # GLM-5-Turbo 是 reasoning 模型，内容可能在 reasoning_content 里
            msg = data["choices"][0]["message"]
            return msg.get("content") or msg.get("reasoning_content") or ""
        except httpx.TimeoutException:
            logger.warning(f"{self.llm_model} API 超时")
            return None
        except Exception as e:
            logger.error(f"调用 {self.llm_model} 失败: {e}")
            return None

    async def _call_model(self, prompt: str) -> Optional[str]:
        """统一调用入口"""
        if not self.use_ollama:
            result = await self._call_llm(prompt)
            if result:
                return result
            logger.warning(f"{self.llm_model} 失败，fallback 到 Ollama")
        return await self._call_ollama(prompt)

    def _parse_json_from_text(self, text: str) -> Optional[Dict]:
        """从文本中提取 JSON"""
        try:
            return json.loads(text)
        except:
            pass
        # JSON 代码块
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        # 花括号
        brace_pattern = r'\{[^{}]*\}'
        match = re.search(brace_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return None

    async def analyze(self, text: str) -> Dict[str, Any]:
        """对新闻文本做情感分析"""
        prompt = f"""判断以下财经新闻的情感倾向。

新闻内容：
{text[:500]}

请分析并返回 JSON 格式：
{{
  "sentiment": "positive/negative/neutral",
  "score": 0.0-1.0,
  "keywords": ["关键词1", "关键词2"]
}}

说明：
- sentiment: positive（正面）、negative（负面）、neutral（中性）
- score: 情感强度（0-1）
- keywords: 影响 sentiment 的关键词（最多3个）

只返回 JSON，不要其他内容。"""

        response_text = await self._call_model(prompt)

        default_result = {'sentiment': 'neutral', 'score': 0.5, 'keywords': []}

        if not response_text:
            logger.warning("情感分析 LLM 未返回结果，使用默认值")
            return default_result

        result = self._parse_json_from_text(response_text)

        if not result:
            logger.warning(f"无法解析情感分析 JSON: {response_text[:200]}")
            return default_result

        # 验证字段
        if 'sentiment' not in result:
            result['sentiment'] = 'neutral'
        if 'score' not in result:
            result['score'] = 0.5
        if 'keywords' not in result:
            result['keywords'] = []

        if result['sentiment'] not in ['positive', 'negative', 'neutral']:
            result['sentiment'] = 'neutral'

        try:
            result['score'] = float(result['score'])
            result['score'] = max(0.0, min(1.0, result['score']))
        except:
            result['score'] = 0.5

        logger.info(f"情感分析完成: {result['sentiment']} ({result['score']})")
        return result

    async def analyze_batch(self, texts: list) -> list:
        results = []
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
        return results

    async def close(self):
        await self.client.aclose()
