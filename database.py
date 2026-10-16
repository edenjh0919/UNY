import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드 (로컬 개발 환경용)
load_dotenv()

def get_env_variable(key_name: str) -> str:
    """Streamlit Secrets 우선 참조 후, 없으면 os.getenv 참조하는 함수"""
    try:
        # 1. Streamlit Secrets 확인
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        # Streamlit 실행 환경이 아닌 경우(예: python database.py 직접 실행 등) 예외 처리
        pass
    
    # 2. 로컬 .env 또는 시스템 환경변수 확인
    return os.getenv(key_name)

# 환경변수 불러오기
SUPABASE_URL = get_env_variable("SUPABASE_URL")
SUPABASE_KEY = get_env_variable("SUPABASE_KEY")

# Supabase 클라이언트 초기화
supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if SUPABASE_URL and SUPABASE_KEY
    else None
)

def get_supabase_client() -> Client:
    """Supabase 인스턴스를 반환하는 함수"""
    if not supabase:
        raise ValueError(
            "DB 연결 실패: SUPABASE_URL 또는 SUPABASE_KEY를 찾을 수 없습니다.\n"
            "Streamlit Cloud의 Settings -> Secrets 설정 또는 .env 파일을 확인해 주세요."
        )
    return supabase

# 데이터베이스 연결 단독 테스트 (터미널에서 python database.py 실행 시)
if __name__ == "__main__":
    try:
        print("🔍 Supabase 연결 테스트 중...")
        print(f"URL 로드 상태: {'성공' if SUPABASE_URL else '실패 (None)'}")
        print(f"KEY 로드 상태: {'성공' if SUPABASE_KEY else '실패 (None)'}")
        
        client = get_supabase_client()
        
        # 'notices' 테이블 연결 테스트
        response = client.table("notices").select("*").limit(1).execute()
        print("🎉 ✅ Supabase DB 연동 성공!")
        print("조회 결과:", response.data)
    except Exception as e:
        print("❌ Supabase DB 연동 실패:")
        print(e)