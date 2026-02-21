"""
LLM客户端封装
统一使用OpenAI格式调用，内置指数退避重试机制以增强鲁棒性
"""

import json
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError

from ..config import Config
from .logger import get_logger

logger = get_logger('echolens.llm_client')


class LLMClient:
    """LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0 # 设置合理的超时时间
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        max_retries: int = 3 # 最大重试次数
    ) -> str:
        """
        发送聊天请求（带重试机制）

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            max_retries: 失败重试次数

        Returns:
            模型响应文本
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        attempt = 0
        while attempt < max_retries:
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            except (APITimeoutError, APIConnectionError, RateLimitError) as e:
                attempt += 1
                if attempt >= max_retries:
                    logger.error(f"LLM API 调用失败，已达到最大重试次数 {max_retries}: {str(e)}")
                    raise Exception(f"LLM API 请求重试{max_retries}次后仍失败: {str(e)}")

                # 指数退避: 1s -> 2s -> 4s
                wait_time = 2 ** (attempt - 1)
                logger.warning(f"LLM API 遇到可恢复错误 ({type(e).__name__})，{wait_time}秒后进行第 {attempt+1} 次重试... 详情: {str(e)}")
                time.sleep(wait_time)
            except APIStatusError as e:
                # 处理 5xx 服务端错误
                if e.status_code >= 500:
                    attempt += 1
                    if attempt >= max_retries:
                        logger.error(f"LLM API 遇到 5xx 错误，已达到最大重试次数: {e.status_code} - {e.message}")
                        raise Exception(f"LLM API 服务端错误重试失败: {e.status_code}")

                    wait_time = 2 ** attempt
                    logger.warning(f"LLM API 服务端错误 {e.status_code}，{wait_time}秒后进行第 {attempt+1} 次重试...")
                    time.sleep(wait_time)
                else:
                    # 4xx 客户端错误通常不应重试（除429限流外，限流已被RateLimitError捕获）
                    logger.error(f"LLM API 客户端请求错误: {e.status_code} - {e.message}")
                    raise
            except Exception as e:
                # 其他未知错误，直接抛出
                logger.error(f"LLM API 发生未知错误: {str(e)}")
                raise

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON
        """
        response_text = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"LLM 响应并非有效 JSON 格式: {e}\n原始响应: {response_text[:200]}...")
            # 优雅降级：如果解析失败，不要让整个系统崩溃，返回一个带有错误信息的字典
            return {"error": "JSON_PARSE_FAILED", "raw_response": response_text[:500]}

