"""
情感分析服务 - 使用本地 Ollama
"""
import httpx
import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情感分析器"""
    
    API_URL = "http://localhost:11434/api/generate"
    MODEL = "qwen2.5:0.5b"
    TIMEOUT = 10.0  # 增加超时时间
    
    def __init__(self):
        """初始化情感分析器"""
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
    
    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        调用 Ollama API
        
        Args:
            prompt: 提示词
            
        Returns:
            模型返回的文本，失败返回 None
        """
        try:
            response = await self.client.post(
                self.API_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.TimeoutException:
            logger.warning("Ollama API 超时")
            return None
        except Exception as e:
            logger.error(f"调用 Ollama 失败: {e}")
            return None
    
    def _parse_json_from_text(self, text: str) -> Optional[Dict]:
        """
        从文本中提取 JSON
        
        Args:
            text: 可能包含 JSON 的文本
            
        Returns:
            解析后的字典，失败返回 None
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试提取 JSON 代码块
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # 尝试提取花括号内容
        brace_pattern = r'\{[^{}]*\}'
        match = re.search(brace_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        return None
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        对新闻文本做情感分析
        
        Args:
            text: 新闻文本
            
        Returns:
            {
                'sentiment': 'positive'/'negative'/'neutral',
                'score': 0.8,
                'keywords': ['关键词1', '关键词2']
            }
        """
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

        response_text = await self._call_ollama(prompt)
        
        # 默认结果
        default_result = {
            'sentiment': 'neutral',
            'score': 0.5,
            'keywords': []
        }
        
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
        
        # 验证 sentiment 值
        if result['sentiment'] not in ['positive', 'negative', 'neutral']:
            result['sentiment'] = 'neutral'
        
        # 验证 score 范围
        try:
            result['score'] = float(result['score'])
            result['score'] = max(0.0, min(1.0, result['score']))
        except:
            result['score'] = 0.5
        
        logger.info(f"情感分析完成: {result['sentiment']} ({result['score']})")
        return result
    
    async def analyze_batch(self, texts: list) -> list:
        """
        批量情感分析
        
        Args:
            texts: 文本列表
            
        Returns:
            情感分析结果列表
        """
        results = []
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
        return results
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
