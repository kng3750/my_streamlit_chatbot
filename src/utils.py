"""공통 유틸리티 함수 모듈"""
import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """로깅 설정"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def format_error_message(error: Exception) -> str:
    """예외를 사용자 친화적인 메시지로 변환"""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # 이미 포맷된 메시지인 경우 그대로 반환 (중복 포맷 방지)
    if "❌" in error_msg or "⏱️" in error_msg or "🌐" in error_msg or "⏰" in error_msg:
        return error_msg
    
    error_msg_lower = error_msg.lower()
    
    # OpenAI API 관련 에러 처리
    if "invalid_api_key" in error_msg_lower or "incorrect api key" in error_msg_lower:
        return f"❌ OpenAI API 키가 유효하지 않습니다.\n\n상세: {error_msg}\n\n💡 .env 파일의 OPENAI_API_KEY를 확인해주세요."
    
    if "authentication" in error_msg_lower or "unauthorized" in error_msg_lower:
        return f"❌ 인증 오류가 발생했습니다.\n\n상세: {error_msg}\n\n💡 .env 파일의 OPENAI_API_KEY가 올바른지 확인해주세요. (공백이나 따옴표 없이)"
    
    if "rate limit" in error_msg_lower or "429" in error_msg:
        return f"⏱️ API 호출 한도에 도달했습니다.\n\n상세: {error_msg}"
    
    if "network" in error_msg_lower or "connection" in error_msg_lower:
        return f"🌐 네트워크 연결 오류가 발생했습니다.\n\n상세: {error_msg}"
    
    if "timeout" in error_msg_lower:
        return f"⏰ 요청 시간이 초과되었습니다.\n\n상세: {error_msg}"
    
    # 일반적인 에러 메시지 (실제 에러 메시지 포함)
    return f"❌ 오류가 발생했습니다: {error_type}\n\n상세: {error_msg}"


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """환경변수 가져오기 (dotenv 사용)"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일을 명시적으로 로드 (override=False로 기존 환경변수 보호)
    load_dotenv(override=False)
    
    # 먼저 시스템 환경변수 확인
    value = os.getenv(key)
    
    # 없으면 .env 파일에서 직접 읽기 시도
    if not value:
        from dotenv import dotenv_values
        env_values = dotenv_values(".env")
        value = env_values.get(key)
    
    # 공백 및 줄바꿈 제거
    if value:
        value = value.strip()
        # 따옴표 제거 (혹시 있을 경우)
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1].strip()
    
    return value if value else default
