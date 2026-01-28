"""Streamlit 웹 챗봇 엔트리 포인트"""
import streamlit as st
import os
#from dotenv import load_dotenv

from src.llm import LLMClient
from src.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from src.ui import render_sidebar, render_chat_history, render_streaming_message
from src.utils import format_error_message, get_env_var, setup_logging

# 로깅 설정
setup_logging()

# 환경변수 로드
#load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="Streamlit Web Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_prompt" not in st.session_state:
    # 환경변수에서 기본값 가져오기, 없으면 기본 프롬프트 사용
    st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT

if "model" not in st.session_state:
    # 환경변수에서 모델 가져오기, 없으면 기본 모델 사용
    env_model = get_env_var("OPENAI_MODEL", DEFAULT_MODEL)
    st.session_state.model = env_model if env_model in ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"] else DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state.temperature = DEFAULT_TEMPERATURE


def main():
    """메인 함수"""
    st.title("🤖 Streamlit Web Chatbot")
    st.caption("OpenAI API를 사용하는 대화형 챗봇")
    
    # 사이드바 렌더링
    selected_model, selected_temperature, system_prompt = render_sidebar(
        default_model=st.session_state.model,
        default_temperature=st.session_state.temperature,
        default_system_prompt=st.session_state.system_prompt,
    )
    
    # 세션 상태 업데이트
    st.session_state.model = selected_model
    st.session_state.temperature = selected_temperature
    st.session_state.system_prompt = system_prompt
    
    # API 키 확인
    api_key = get_env_var("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        st.info("💡 .env.example 파일을 참고하여 .env 파일을 생성하세요.")
        st.code("OPENAI_API_KEY=sk-your-api-key-here", language="bash")
        
        # 디버깅 정보
        with st.expander("🔍 디버깅 정보"):
            import os
            st.write(f"현재 작업 디렉토리: {os.getcwd()}")
            st.write(f".env 파일 존재 여부: {os.path.exists('.env')}")
            if os.path.exists('.env'):
                try:
                    with open('.env', 'r', encoding='utf-8') as f:
                        env_content = f.read()
                        st.write("📄 .env 파일 내용 (마스킹됨):")
                        # API 키 부분만 마스킹
                        masked_content = env_content
                        if 'OPENAI_API_KEY=' in masked_content:
                            lines = masked_content.split('\n')
                            for i, line in enumerate(lines):
                                if line.startswith('OPENAI_API_KEY='):
                                    key_part = line.split('=', 1)[1] if '=' in line else ''
                                    if len(key_part) > 20:
                                        masked_key = f"{key_part[:10]}...{key_part[-4:]}"
                                    else:
                                        masked_key = key_part[:10] + "..." if len(key_part) > 10 else key_part
                                    lines[i] = f"OPENAI_API_KEY={masked_key}"
                            masked_content = '\n'.join(lines)
                        st.code(masked_content, language="bash")
                except Exception as e:
                    st.write(f"❌ .env 파일 읽기 오류: {e}")
            env_key = os.getenv("OPENAI_API_KEY")
            st.write(f"시스템 환경변수 OPENAI_API_KEY: {'설정됨' if env_key else '설정되지 않음'}")
        return
    
    # API 키 정리 및 검증
    api_key_clean = api_key.strip()
    # 따옴표 제거
    if (api_key_clean.startswith('"') and api_key_clean.endswith('"')) or (api_key_clean.startswith("'") and api_key_clean.endswith("'")):
        api_key_clean = api_key_clean[1:-1].strip()
    
    # API 키 검증
    validation_errors = []
    if not api_key_clean.startswith("sk-"):
        validation_errors.append("⚠️ API 키는 'sk-'로 시작해야 합니다.")
    if len(api_key_clean) < 20:
        validation_errors.append(f"⚠️ API 키가 너무 짧습니다. (현재 길이: {len(api_key_clean)} 문자)")
    if len(api_key_clean) > 300:
        validation_errors.append(f"⚠️ API 키가 너무 깁니다. (현재 길이: {len(api_key_clean)} 문자)")
    
    if validation_errors:
        st.warning("API 키 검증 경고:")
        for error in validation_errors:
            st.write(error)
        st.info(f"💡 키 시작: {api_key_clean[:15]}...")
        st.info(f"💡 키 끝: ...{api_key_clean[-10:]}")
        st.info(f"💡 키 길이: {len(api_key_clean)} 문자")
    
    # API 키 상태 표시 (사이드바에)
    with st.sidebar:
        st.divider()
        key_status = "✅ 설정됨" if api_key_clean.startswith("sk-") and 20 <= len(api_key_clean) <= 300 else "⚠️ 확인 필요"
        st.caption(f"🔑 API 키: {key_status}")
        if api_key_clean.startswith("sk-"):
            st.caption(f"📏 길이: {len(api_key_clean)} 문자")
    
    # 채팅 히스토리 렌더링
    render_chat_history(st.session_state.messages)
    
    # 사용자 입력 처리
    user_input = st.chat_input("메시지를 입력하세요...")
    
    if user_input:
        # 사용자 메시지를 세션에 추가하고 즉시 표시
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # 사용자 메시지 렌더링
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 어시스턴트 응답 생성 (스트리밍)
        try:
            # LLM 클라이언트 초기화 (API 키 재확인)
            try:
                llm_client = LLMClient()
            except ValueError as ve:
                st.error(f"❌ API 키 설정 오류: {str(ve)}")
                with st.expander("🔍 API 키 확인 방법"):
                    st.write("""
                    1. **.env 파일 확인**
                       - 프로젝트 루트 디렉토리에 `.env` 파일이 있는지 확인하세요
                       - 파일 내용: `OPENAI_API_KEY=sk-proj-...` (공백 없이)
                    
                    2. **API 키 형식 확인**
                       - `sk-proj-` 또는 `sk-`로 시작해야 합니다
                       - 전체 키를 복사했는지 확인하세요 (일부만 복사되지 않았는지)
                       - 따옴표나 공백이 없어야 합니다
                    
                    3. **파일 저장 확인**
                       - .env 파일을 저장했는지 확인하세요
                       - Streamlit 앱을 재시작하세요 (환경변수는 앱 시작 시 로드됩니다)
                    
                    4. **API 키 확인**
                       - https://platform.openai.com/account/api-keys 에서 확인하세요
                    """)
                return
            
            # 메시지 포맷 준비 (system + history)
            messages_for_api = [
                {"role": "system", "content": st.session_state.system_prompt}
            ]
            # user/assistant 메시지만 추가 (system 제외)
            for msg in st.session_state.messages:
                messages_for_api.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # 스트리밍 응답 생성
            assistant_placeholder = render_streaming_message("assistant")
            full_response = ""
            
            with st.spinner("답변을 생성하는 중..."):
                try:
                    for chunk in llm_client.stream_chat(
                        messages=messages_for_api,
                        model=st.session_state.model,
                        temperature=st.session_state.temperature,
                    ):
                        full_response += chunk
                        assistant_placeholder.markdown(full_response + "▌")
                    
                    # 최종 응답 표시 (커서 제거)
                    assistant_placeholder.markdown(full_response)
                    
                    # 어시스턴트 메시지를 세션에 추가
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
                except Exception as e:
                    # 예외 메시지를 그대로 표시 (이미 포맷된 경우)
                    error_msg = str(e)
                    assistant_placeholder.error(f"❌ 오류 발생")
                    # 상세 에러 메시지를 expander로 표시
                    with st.expander("🔍 상세 에러 정보", expanded=True):
                        st.error(error_msg)
                    st.error(error_msg)
                    
        except ValueError as e:
            st.error(f"❌ 설정 오류: {str(e)}")
            with st.expander("🔍 상세 정보", expanded=True):
                st.code(str(e), language="text")
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ 예상치 못한 오류 발생")
            with st.expander("🔍 상세 에러 정보", expanded=True):
                st.error(error_msg)
                st.code(f"에러 타입: {type(e).__name__}\n에러 메시지: {error_msg}", language="text")


if __name__ == "__main__":
    main()
