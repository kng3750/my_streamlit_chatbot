"""프롬프트 및 기본 설정 모듈"""

# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """당신은 친절하고 도움이 되는 AI 어시스턴트입니다. 
사용자의 질문에 정확하고 유용한 답변을 제공해주세요."""

# 사용 가능한 모델 목록
AVAILABLE_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

# 기본 모델
DEFAULT_MODEL = "gpt-4o-mini"

# 기본 temperature
DEFAULT_TEMPERATURE = 0.7
