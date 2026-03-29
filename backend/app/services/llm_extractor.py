"""
LLM 实体和关系抽取服务 - 使用本地 Ollama
"""
import httpx
import json
import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class LLMExtractor:
    """用 LLM API 做实体和关系抽取"""
    
    API_URL = "http://localhost:11434/api/generate"
    MODEL = "qwen2.5:0.5b"
    TIMEOUT = 10.0  # 增加超时时间
    
    def __init__(self):
        """初始化 LLM 抽取器"""
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
    
    async def extract(self, text: str) -> Dict[str, Any]:
        """
        调用本地 LLM 抽取实体和关系
        
        Args:
            text: 新闻文本
            
        Returns:
            {
                'entities': [{'name': '...', 'type': 'company/person/industry', ...}],
                'relations': [{'from': '...', 'to': '...', 'type': '...', ...}]
            }
            失败时返回 {'entities': [], 'relations': []}
        """
        prompt = f"""从以下财经新闻中提取实体和关系。

实体类型：
- company: 公司
- person: 人物
- industry: 行业

关系类型：
- invests_in: 投资
- partner_of: 合作
- competes_with: 竞争
- supplies_to: 供应

新闻内容：
{text[:1000]}

请以 JSON 格式返回，格式如下：
{{
  "entities": [
    {{"name": "实体名", "type": "company/person/industry"}}
  ],
  "relations": [
    {{"from": "实体1", "to": "实体2", "type": "关系类型"}}
  ]
}}

只返回 JSON，不要其他内容。"""

        response_text = await self._call_ollama(prompt)
        
        if not response_text:
            logger.warning("LLM 未返回结果，将使用规则方案")
            return {'entities': [], 'relations': []}
        
        result = self._parse_json_from_text(response_text)
        
        if not result:
            logger.warning(f"无法解析 LLM 返回的 JSON: {response_text[:200]}")
            return {'entities': [], 'relations': []}
        
        # 验证结构
        if 'entities' not in result:
            result['entities'] = []
        if 'relations' not in result:
            result['relations'] = []
        
        logger.info(f"LLM 抽取成功: {len(result['entities'])} 个实体, {len(result['relations'])} 个关系")
        return result
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
