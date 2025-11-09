from typing import Dict, Any, Iterator, Optional, List
from abc import ABC, abstractmethod
from pydantic import BaseModel
import os


class LLMConfig(BaseModel):
    """LLM配置"""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class LLMResponse(BaseModel):
    """LLM响应"""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


class LLMProvider(ABC):
    """LLM提供商抽象接口"""
    
    @abstractmethod
    async def generate(self, prompt: str, config: LLMConfig) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, config: LLMConfig) -> Iterator[str]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI提供商实现"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set")
    
    async def generate(self, prompt: str, config: LLMConfig) -> str:
        """
        使用OpenAI API生成文本
        
        注意: 这是一个简化的实现,实际使用时需要安装openai库
        """
        # TODO: 实际实现需要使用openai库
        # from openai import AsyncOpenAI
        # client = AsyncOpenAI(api_key=self.api_key)
        # response = await client.chat.completions.create(
        #     model=config.model,
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=config.temperature,
        #     max_tokens=config.max_tokens
        # )
        # return response.choices[0].message.content
        
        return f"[模拟OpenAI响应] 收到提示: {prompt[:50]}..."
    
    async def stream(self, prompt: str, config: LLMConfig) -> Iterator[str]:
        """流式生成"""
        # TODO: 实现流式生成
        yield f"[模拟流式响应] {prompt[:50]}..."
    
    async def embed(self, text: str) -> List[float]:
        """生成嵌入向量"""
        # TODO: 实现嵌入向量生成
        return [0.0] * 1536  # 模拟返回1536维向量


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) 提供商实现"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set")
    
    async def generate(self, prompt: str, config: LLMConfig) -> str:
        """使用Anthropic API生成文本"""
        # TODO: 实现Anthropic API调用
        return f"[模拟Anthropic响应] 收到提示: {prompt[:50]}..."
    
    async def stream(self, prompt: str, config: LLMConfig) -> Iterator[str]:
        """流式生成"""
        yield f"[模拟流式响应] {prompt[:50]}..."
    
    async def embed(self, text: str) -> List[float]:
        """生成嵌入向量"""
        return [0.0] * 1536


class LLMService:
    """
    LLM服务统一接口
    支持多个提供商和自动fallback
    """
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = "openai"
        self.fallback_chain = ["openai", "anthropic"]
        
        # 初始化提供商
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化所有提供商"""
        self.providers["openai"] = OpenAIProvider()
        self.providers["anthropic"] = AnthropicProvider()
    
    async def generate(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        config: Optional[LLMConfig] = None
    ) -> LLMResponse:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            model: 模型名称
            config: LLM配置
            
        Returns:
            LLMResponse: LLM响应
        """
        if config is None:
            config = LLMConfig(model=model or "gpt-3.5-turbo")
        
        provider_name = self.default_provider
        provider = self.providers.get(provider_name)
        
        if not provider:
            raise ValueError(f"Provider not found: {provider_name}")
        
        try:
            content = await provider.generate(prompt, config)
            return LLMResponse(
                content=content,
                model=config.model,
                tokens_used=0  # TODO: 计算实际token使用量
            )
        except Exception as e:
            # TODO: 实现fallback机制
            print(f"LLM generation failed: {e}")
            raise
    
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        config: Optional[LLMConfig] = None
    ) -> Iterator[str]:
        """
        流式生成文本
        
        Args:
            prompt: 输入提示
            model: 模型名称
            config: LLM配置
            
        Yields:
            str: 生成的文本片段
        """
        if config is None:
            config = LLMConfig(model=model or "gpt-3.5-turbo")
        
        provider = self.providers.get(self.default_provider)
        
        if not provider:
            raise ValueError(f"Provider not found: {self.default_provider}")
        
        async for chunk in provider.stream(prompt, config):
            yield chunk
    
    async def embed(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 输入文本
            model: 嵌入模型名称
            
        Returns:
            List[float]: 嵌入向量
        """
        provider = self.providers.get(self.default_provider)
        
        if not provider:
            raise ValueError(f"Provider not found: {self.default_provider}")
        
        return await provider.embed(text)
    
    def switch_provider(self, provider_name: str):
        """
        切换LLM提供商
        
        Args:
            provider_name: 提供商名称
        """
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        self.default_provider = provider_name
        print(f"Switched to provider: {provider_name}")