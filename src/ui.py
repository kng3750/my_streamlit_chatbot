"""채팅 UI 렌더링 함수 모듈"""
import streamlit as st
from typing import Optional


def render_sidebar(
    default_model: str,
    default_temperature: float,
    default_system_prompt: str,
) -> tuple[str, float, str]:
    """
    사이드바 UI 렌더링
    
    Returns:
        tuple: (selected_model, temperature, system_prompt)
    """
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 모델 선택
        model = st.selectbox(
            "모델 선택",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0 if default_model == "gpt-4o-mini" else 
                  (1 if default_model == "gpt-4o" else 
                   (2 if default_model == "gpt-4-turbo" else 3)),
            key="model_select",
        )
        
        # Temperature 슬라이더
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=default_temperature,
            step=0.1,
            help="값이 높을수록 더 창의적인 응답을 생성합니다.",
            key="temperature_slider",
        )
        
        st.divider()
        
        # 대화 초기화 버튼
        if st.button("🗑️ 대화 초기화", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.system_prompt = default_system_prompt
            st.rerun()
        
        st.divider()
        
        # 시스템 프롬프트 편집
        st.subheader("시스템 프롬프트")
        system_prompt = st.text_area(
            "시스템 프롬프트를 수정하세요",
            value=default_system_prompt,
            height=150,
            key="system_prompt_editor",
            help="AI의 행동과 응답 스타일을 정의하는 프롬프트입니다.",
        )
        
        return model, temperature, system_prompt


def render_message(message: dict):
    """
    개별 메시지 렌더링
    
    Args:
        message: {"role": "user" | "assistant", "content": str}
    """
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role):
        st.markdown(content)


def render_chat_history(messages: list[dict]):
    """
    채팅 히스토리 렌더링
    
    Args:
        messages: 메시지 리스트
    """
    for message in messages:
        render_message(message)


def render_streaming_message(role: str = "assistant"):
    """
    스트리밍 중인 메시지를 위한 placeholder 반환
    
    Args:
        role: 메시지 역할
        
    Returns:
        streamlit.delta_generator.DeltaGenerator: placeholder 객체
    """
    return st.chat_message(role).empty()
