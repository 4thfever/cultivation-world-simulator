"""LLM 相关异常定义"""


class LLMError(Exception):
    """LLM 相关错误的基类"""
    
    def __init__(self, message: str, *, cause: Exception | None = None, **context):
        super().__init__(message)
        self.cause = cause
        self.context = context


class ParseError(LLMError):
    """JSON 解析失败"""
    
    def __init__(self, message: str, *, raw_text: str = ""):
        super().__init__(message, raw_text=raw_text)
        self.raw_text = raw_text


class ConfigError(LLMError):
    """配置错误"""
    pass

