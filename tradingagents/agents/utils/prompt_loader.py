#!/usr/bin/env python3
"""
Prompt加载器和管理器
提供统一的Prompt加载接口，支持从文件或模板加载
"""

import os
from pathlib import Path
from typing import Dict, Optional
from tradingagents.agents.prompt_templates import (
    STANDARD_BULL_PROMPT_ZH, STANDARD_BULL_PROMPT_EN,
    STANDARD_BEAR_PROMPT_ZH, STANDARD_BEAR_PROMPT_EN,
    STANDARD_CONSERVATIVE_PROMPT_ZH,
    STANDARD_AGGRESSIVE_PROMPT_ZH
)


class PromptLoader:
    """Prompt加载器"""
    
    # 内置Prompt映射表
    BUILT_IN_PROMPTS = {
        "bull_researcher": {
            "zh": STANDARD_BULL_PROMPT_ZH,
            "en": STANDARD_BULL_PROMPT_EN
        },
        "bear_researcher": {
            "zh": STANDARD_BEAR_PROMPT_ZH,
            "en": STANDARD_BEAR_PROMPT_EN
        },
        "conservative_analyst": {
            "zh": STANDARD_CONSERVATIVE_PROMPT_ZH,
            "en": ""  # 暂无英文版
        },
        "aggressive_analyst": {
            "zh": STANDARD_AGGRESSIVE_PROMPT_ZH,
            "en": ""  # 暂无英文版
        }
    }
    
    def __init__(self, prompts_dir: Optional[str] = None) -> None:
        """
        初始化Prompt加载器
        
        Args:
            prompts_dir: 自定义Prompt文件目录（可选）
        """
        self.prompts_dir = Path(prompts_dir) if prompts_dir else None
    
    def load_prompt(
        self,
        prompt_name: str,
        language: str = "zh",
        fallback_to_builtin: bool = True
    ) -> str:
        """
        加载Prompt
        
        Args:
            prompt_name: Prompt名称（如 "bull_researcher"）
            language: 语言代码（"zh" 或 "en"）
            fallback_to_builtin: 是否回退到内置Prompt
            
        Returns:
            Prompt文本
            
        Raises:
            FileNotFoundError: 如果找不到Prompt且不允许回退
        """
        # 1. 尝试从文件加载（如果配置了目录）
        if self.prompts_dir:
            file_path = self.prompts_dir / f"{prompt_name}_{language}.txt"
            if file_path.exists():
                return file_path.read_text(encoding="utf-8")
        
        # 2. 回退到内置Prompt
        if fallback_to_builtin:
            if prompt_name in self.BUILT_IN_PROMPTS:
                return self.BUILT_IN_PROMPTS[prompt_name].get(language, "")
        
        # 3. 找不到Prompt
        raise FileNotFoundError(
            f"Prompt not found: {prompt_name} (language: {language})"
        )
    
    def get_prompts(self, prompt_name: str) -> Dict[str, str]:
        """
        获取指定Prompt的所有语言版本
        
        Args:
            prompt_name: Prompt名称
            
        Returns:
            包含所有语言版本的字典 {"zh": "...", "en": "..."}
        """
        return {
            "zh": self.load_prompt(prompt_name, "zh"),
            "en": self.load_prompt(prompt_name, "en")
        }


# 全局默认加载器（使用内置Prompt）
_default_loader = PromptLoader()


def get_prompt(prompt_name: str, language: str = "zh") -> str:
    """
    便捷函数：加载Prompt
    
    Args:
        prompt_name: Prompt名称
        language: 语言代码
        
    Returns:
        Prompt文本
    """
    return _default_loader.load_prompt(prompt_name, language)


def get_prompts_dict(prompt_name: str) -> Dict[str, str]:
    """
    便捷函数：获取所有语言版本的Prompt
    
    Args:
        prompt_name: Prompt名称
        
    Returns:
        包含所有语言版本的字典
    """
    return _default_loader.get_prompts(prompt_name)
