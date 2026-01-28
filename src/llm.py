"""OpenAI LLM 호출 및 스트리밍 처리 모듈"""
import os
from typing import Iterator, Optional
from openai import OpenAI
from openai import APIError, APIConnectionError, APITimeoutError, RateLimitError

from src.utils import format_error_message, get_env_var


class LLMClient:
    """OpenAI API 클라이언트 래퍼"""
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        api_key = get_env_var("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        # API 키에서 공백 및 줄바꿈 제거
        api_key = api_key.strip()
        
        # 따옴표 제거 (혹시 있을 경우)
        if (api_key.startswith('"') and api_key.endswith('"')) or (api_key.startswith("'") and api_key.endswith("'")):
            api_key = api_key[1:-1].strip()
        
        if not api_key.startswith("sk-"):
            raise ValueError(f"OPENAI_API_KEY 형식이 올바르지 않습니다. (시작: {api_key[:10]}...)")
        
        # API 키 길이 확인 (일반적으로 50자 이상)
        if len(api_key) < 20:
            raise ValueError(f"OPENAI_API_KEY가 너무 짧습니다. (길이: {len(api_key)} 문자)")
        
        # API 키 정보 저장 (디버깅용)
        self.api_key_preview = f"{api_key[:15]}...{api_key[-10:]}" if len(api_key) > 25 else api_key[:15]
        self.api_key_length = len(api_key)
        
        self.client = OpenAI(api_key=api_key)
    
    def stream_chat(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """
        스트리밍 방식으로 채팅 응답 생성
        
        Args:
            messages: 대화 메시지 리스트 (OpenAI 포맷)
            model: 사용할 모델명
            temperature: 온도 설정
            
        Yields:
            str: 스트리밍된 텍스트 청크
            
        Raises:
            ValueError: API 키가 없을 때
            Exception: API 호출 실패 시
        """
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except RateLimitError as e:
            error_detail = f"{e.message}" if hasattr(e, 'message') else str(e)
            raise Exception(f"⏱️ API 호출 한도 초과: {error_detail}")
        except APIConnectionError as e:
            error_detail = f"{e.message}" if hasattr(e, 'message') else str(e)
            raise Exception(f"🌐 네트워크 연결 오류: {error_detail}")
        except APITimeoutError as e:
            error_detail = f"{e.message}" if hasattr(e, 'message') else str(e)
            raise Exception(f"⏰ 요청 시간 초과: {error_detail}")
        except APIError as e:
            # OpenAI API 에러의 모든 속성 확인
            error_detail = ""
            error_code = "Unknown"
            error_type = "APIError"
            error_param = None
            
            # 에러 객체의 모든 속성 확인
            if hasattr(e, 'message'):
                error_detail = str(e.message)
            elif hasattr(e, 'body'):
                error_detail = str(e.body)
            else:
                error_detail = str(e)
            
            if hasattr(e, 'code'):
                error_code = str(e.code)
            if hasattr(e, 'type'):
                error_type = str(e.type)
            if hasattr(e, 'param'):
                error_param = str(e.param)
            
            # 전체 에러 정보 수집
            error_info = [f"에러 타입: {error_type}", f"에러 코드: {error_code}"]
            if error_param:
                error_info.append(f"파라미터: {error_param}")
            error_info.append(f"상세 메시지: {error_detail}")
            
            # 사용된 API 키 정보 추가 (디버깅용)
            if hasattr(self, 'api_key_preview'):
                error_info.append(f"\n🔍 사용된 API 키 정보:")
                error_info.append(f"   - 키 시작: {self.api_key_preview.split('...')[0] if '...' in self.api_key_preview else self.api_key_preview}")
                error_info.append(f"   - 키 끝: ...{self.api_key_preview.split('...')[-1] if '...' in self.api_key_preview else ''}")
                error_info.append(f"   - 키 길이: {self.api_key_length} 문자")
            
            error_full_msg = "\n".join(error_info)
            
            # 인증 관련 에러인 경우
            if error_code == "invalid_api_key" or "invalid_api_key" in error_detail.lower() or "authentication" in error_detail.lower():
                # 에러 메시지에서 언급된 키 추출 시도
                error_key_hint = ""
                if "Incorrect API key provided:" in error_detail:
                    try:
                        import re
                        match = re.search(r'sk-[^\s\*]+', error_detail)
                        if match:
                            mentioned_key = match.group(0)
                            if len(mentioned_key) > 20:
                                error_key_hint = f"\n⚠️ 에러 메시지에서 언급된 키: {mentioned_key[:15]}...{mentioned_key[-10:]}"
                            else:
                                error_key_hint = f"\n⚠️ 에러 메시지에서 언급된 키: {mentioned_key}"
                    except:
                        pass
                
                raise Exception(f"❌ API 키 인증 실패\n\n{error_full_msg}{error_key_hint}\n\n💡 해결 방법:\n   1. .env 파일에서 OPENAI_API_KEY를 확인하세요\n   2. API 키 전체를 복사했는지 확인하세요 (일부만 복사되지 않았는지)\n   3. 공백이나 따옴표가 없는지 확인하세요\n   4. https://platform.openai.com/account/api-keys 에서 새 키를 생성해보세요\n   5. Streamlit 앱을 재시작하세요")
            
            raise Exception(f"❌ OpenAI API 오류\n\n{error_full_msg}")
        except Exception as e:
            raise Exception(format_error_message(e))
    
    def chat(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ) -> str:
        """
        일반 방식으로 채팅 응답 생성 (비스트리밍)
        
        Args:
            messages: 대화 메시지 리스트 (OpenAI 포맷)
            model: 사용할 모델명
            temperature: 온도 설정
            
        Returns:
            str: 완전한 응답 텍스트
            
        Raises:
            ValueError: API 키가 없을 때
            Exception: API 호출 실패 시
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            
            return response.choices[0].message.content
            
        except RateLimitError as e:
            error_detail = f"{e.message}" if hasattr(e, 'message') else str(e)
            raise Exception(f"⏱️ API 호출 한도 초과: {error_detail}")
        except APIConnectionError as e:
            error_detail = f"{e.message}" if hasattr(e, 'message') else str(e)
            raise Exception(f"🌐 네트워크 연결 오류: {error_detail}")
        except APITimeoutError as e:
            error_detail = f"{e.message}" if hasattr(e, 'message') else str(e)
            raise Exception(f"⏰ 요청 시간 초과: {error_detail}")
        except APIError as e:
            # OpenAI API 에러의 모든 속성 확인
            error_detail = ""
            error_code = "Unknown"
            error_type = "APIError"
            error_param = None
            
            # 에러 객체의 모든 속성 확인
            if hasattr(e, 'message'):
                error_detail = str(e.message)
            elif hasattr(e, 'body'):
                error_detail = str(e.body)
            else:
                error_detail = str(e)
            
            if hasattr(e, 'code'):
                error_code = str(e.code)
            if hasattr(e, 'type'):
                error_type = str(e.type)
            if hasattr(e, 'param'):
                error_param = str(e.param)
            
            # 전체 에러 정보 수집
            error_info = [f"에러 타입: {error_type}", f"에러 코드: {error_code}"]
            if error_param:
                error_info.append(f"파라미터: {error_param}")
            error_info.append(f"상세 메시지: {error_detail}")
            
            # 사용된 API 키 정보 추가 (디버깅용)
            if hasattr(self, 'api_key_preview'):
                error_info.append(f"\n🔍 사용된 API 키 정보:")
                error_info.append(f"   - 키 시작: {self.api_key_preview.split('...')[0] if '...' in self.api_key_preview else self.api_key_preview}")
                error_info.append(f"   - 키 끝: ...{self.api_key_preview.split('...')[-1] if '...' in self.api_key_preview else ''}")
                error_info.append(f"   - 키 길이: {self.api_key_length} 문자")
            
            error_full_msg = "\n".join(error_info)
            
            # 인증 관련 에러인 경우
            if error_code == "invalid_api_key" or "invalid_api_key" in error_detail.lower() or "authentication" in error_detail.lower():
                # 에러 메시지에서 언급된 키 추출 시도
                error_key_hint = ""
                if "Incorrect API key provided:" in error_detail:
                    try:
                        import re
                        match = re.search(r'sk-[^\s\*]+', error_detail)
                        if match:
                            mentioned_key = match.group(0)
                            if len(mentioned_key) > 20:
                                error_key_hint = f"\n⚠️ 에러 메시지에서 언급된 키: {mentioned_key[:15]}...{mentioned_key[-10:]}"
                            else:
                                error_key_hint = f"\n⚠️ 에러 메시지에서 언급된 키: {mentioned_key}"
                    except:
                        pass
                
                raise Exception(f"❌ API 키 인증 실패\n\n{error_full_msg}{error_key_hint}\n\n💡 해결 방법:\n   1. .env 파일에서 OPENAI_API_KEY를 확인하세요\n   2. API 키 전체를 복사했는지 확인하세요 (일부만 복사되지 않았는지)\n   3. 공백이나 따옴표가 없는지 확인하세요\n   4. https://platform.openai.com/account/api-keys 에서 새 키를 생성해보세요\n   5. Streamlit 앱을 재시작하세요")
            
            raise Exception(f"❌ OpenAI API 오류\n\n{error_full_msg}")
        except Exception as e:
            raise Exception(format_error_message(e))
