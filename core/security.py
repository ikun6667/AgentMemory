"""安全过滤模块：注入检测 + 敏感信息脱敏"""

import re
from typing import Tuple


class SecurityFilter:
    """安全过滤器：检测提示注入攻击，脱敏敏感信息"""
    
    # 注入特征关键词/模式
    INJECTION_PATTERNS = [
        r"忽略之前",
        r"ignore previous",
        r"ignore all",
        r"无视指令",
        r"你现在是",
        r"you are now",
        r"act as",
        r"扮演",
        r"system:",
        r"assistant:",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\]",
        r"\[/INST\]",
    ]
    
    # 敏感信息正则
    SENSITIVE_PATTERNS = {
        "phone": r"1[3-9]\d{9}",
        "id_card": r"\d{17}[\dXx]",
        "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "bank_card": r"\d{16,19}",
        "address": r"(?:北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|重庆)[市区](?:[^\s,，。]{2,10}(?:路|街|号|弄|栋|幢|室))",
    }
    
    def check_injection(self, content: str) -> Tuple[bool, str]:
        """
        检查是否含注入攻击
        
        Returns:
            (is_injection, error_message)
        """
        content_lower = content.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, content_lower):
                return True, f"检测到注入特征: {pattern}"
        return False, ""
    
    def sanitize(self, content: str) -> str:
        """脱敏敏感信息"""
        result = content
        for name, pattern in self.SENSITIVE_PATTERNS.items():
            result = re.sub(pattern, f"[{name}_hidden]", result)
        return result
    
    def process(self, content: str) -> Tuple[bool, str, str]:
        """
        完整处理流程
        
        Returns:
            (is_safe, processed_content, error_message)
        """
        # 1. 检查注入
        is_injection, error_msg = self.check_injection(content)
        if is_injection:
            return False, "", error_msg
        
        # 2. 脱敏
        sanitized = self.sanitize(content)
        return True, sanitized, ""
    
    def extract_sensitive_info(self, content: str) -> dict:
        """提取内容中的敏感信息（用于审计）"""
        found = {}
        for name, pattern in self.SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, content)
            if matches:
                found[name] = matches
        return found
