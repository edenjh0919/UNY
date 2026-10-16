import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv()

# ⭕ 올바른 코드: .env 파일에 적힌 '변수 이름'을 따옴표 안에 넣어주어야 합니다.
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

# 클라이언트 생성
supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if SUPABASE_URL and SUPABASE_KEY
    else None
)

def get_supabase_client() -> Client:
    """Supabase 인스턴스를 반환하는 함수"""
    if not supabase:
        raise ValueError(
            "Supabase 클라이언트가 초기화되지 않았습니다. .env 파일의 SUPABASE_URL과 SUPABASE_KEY를 확인하세요."
        )
    return supabase

# 데이터베이스 연결 단독 테스트
if __name__ == "__main__":
    try:
        print("🔍 Supabase 연결 테스트 중...")
        client = get_supabase_client()
        
        # 'notices' 테이블 연결 테스트
        response = client.table("notices").select("*").limit(1).execute()
        print("🎉 ✅ Supabase DB 연동 성공!")
        print("조회 결과:", response.data)
    except Exception as e:
        print("❌ Supabase DB 연동 실패:")
        print(e)