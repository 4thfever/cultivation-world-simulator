"""
通用日志模块
功能：
1. 自动记录各种调用的输入和输出（目前主要用于LLM）
2. 启动时自动删除一周以前的日志文件
3. 日志文件按日期分组
"""

import logging
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from src.utils.config import CONFIG

class Logger:
    """通用日志记录器"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志记录器
        
        Args:
            log_dir: 日志文件存储目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 清理旧日志文件
        self._cleanup_old_logs()
        
        # 设置当前日志文件
        self._setup_current_logger()
    
    def _cleanup_old_logs(self):
        """删除一周以前的日志文件"""
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                # 从文件名中提取日期
                date_str = log_file.stem.split("_")[-1]  # 取最后一部分作为日期
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    print(f"已删除过期日志文件: {log_file}")
            except (ValueError, OSError) as e:
                print(f"处理日志文件 {log_file} 时出错: {e}")
    
    def _setup_current_logger(self):
        """设置当前日期的日志记录器"""
        current_date = datetime.now().strftime("%Y%m%d")
        log_filename = f"{current_date}.log"
        self.log_file_path = self.log_dir / log_filename
        
        # 创建日志记录器
        self.logger = logging.getLogger(f"logger_{current_date}")
        self.logger.setLevel(logging.INFO)
        
        # 清除现有的处理器（避免重复记录）
        self.logger.handlers.clear()
        
        # 创建文件处理器
        handler = logging.FileHandler(
            self.log_file_path,
            encoding='utf-8',
            mode='a'
        )
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
        # 不向根日志记录器传播
        self.logger.propagate = False
        
        # 记录版本号
        if hasattr(CONFIG, "meta") and hasattr(CONFIG.meta, "version"):
            self.logger.info(f"========== Game Start (Version: {CONFIG.meta.version}) ==========")
        else:
            self.logger.info("========== Game Start (Version: Unknown) ==========")
    
    def log_llm_interaction(self, 
                          model_name: str,
                          prompt: str, 
                          response: str,
                          duration: Optional[float] = None,
                          additional_info: Optional[dict] = None):
        """
        记录LLM交互
        
        Args:
            model_name: 使用的模型名称
            prompt: 输入的提示词
            response: LLM的响应
            duration: 调用耗时（秒）
            additional_info: 额外信息
        """
        # 机器可读的摘要（不包含大段文本，避免 JSON 转义导致 \ 混杂）
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "duration": duration
        }
        
        if additional_info:
            log_data.update(additional_info)
        
        # 记录可解析的 JSON 摘要
        log_message = f"LLM_INTERACTION: {json.dumps(log_data, ensure_ascii=False)}"
        self.logger.info(log_message)

        # 记录更友好的原始多行文本，避免引号被转义
        self.logger.info("LLM_PROMPT:\n%s", prompt)
        self.logger.info("LLM_RESPONSE:\n%s", response)
    
    def log_error(self, error_message: str, prompt: str = None):
        """
        记录错误
        
        Args:
            error_message: 错误信息
            prompt: 相关的提示词（可选）
        """
        # 错误摘要（不含原始 prompt，避免转义干扰）
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
        }

        log_message = f"LLM_ERROR: {json.dumps(log_data, ensure_ascii=False)}"
        self.logger.error(log_message)

        # 如提供 prompt，追加原始多行文本便于排查
        if prompt:
            self.logger.error("LLM_ERROR_PROMPT:\n%s", prompt)
    
    def get_today_stats(self) -> dict:
        """
        获取今日统计信息
        
        Returns:
            dict: 包含今日调用次数、总耗时等信息
        """
        if not self.log_file_path.exists():
            return {
                "total_calls": 0,
                "total_duration": 0,
                "total_prompt_length": 0,
                "total_response_length": 0,
                "errors": 0
            }
        
        stats = {
            "total_calls": 0,
            "total_duration": 0,
            "total_prompt_length": 0,
            "total_response_length": 0,
            "errors": 0
        }
        
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "LLM_INTERACTION:" in line:
                    try:
                        json_str = line.split("LLM_INTERACTION: ", 1)[1]
                        data = json.loads(json_str)
                        stats["total_calls"] += 1
                        stats["total_duration"] += data.get("duration", 0) or 0
                        stats["total_prompt_length"] += data.get("prompt_length", 0)
                        stats["total_response_length"] += data.get("response_length", 0)
                    except (json.JSONDecodeError, IndexError):
                        pass
                elif "LLM_ERROR:" in line:
                    stats["errors"] += 1
        
        return stats


# 全局日志记录器实例
_logger = None

def get_logger() -> Logger:
    """获取全局日志记录器实例"""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger

# LLM专用的便捷函数
def log_llm_call(model_name: str, prompt: str, response: str, duration: float = None):
    """便捷函数：记录LLM调用"""
    logger = get_logger()
    logger.log_llm_interaction(model_name, prompt, response, duration)

def log_llm_error(error_message: str, prompt: str = None):
    """便捷函数：记录LLM错误"""
    logger = get_logger()
    logger.log_error(error_message, prompt)