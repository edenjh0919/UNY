from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uvicorn

from database import get_supabase_client
from scheduler import run_daily_pipeline

app = FastAPI(
    title="InfoCatch API",
    description="대학생·취준생 맞춤형 정보 통합 관리 및 이메일 알림 시스템 REST API",
    version="1.0.0"
)

# 데이터 검증용 Pydantic 모델
class UserRegisterRequest(BaseModel):
    email: EmailStr
    keywords: List[str]

class UserResponse(BaseModel):
    id: int
    email: str
    keywords: List[str]
    is_active: bool

# --- API 엔드포인트 ---

@app.get("/", summary="서버 상태 확인")
def root():
    return {"status": "online", "message": "InfoCatch API Server가 정상 작동 중입니다."}


@app.get("/notices", summary="공지사항 목록 및 검색 조회")
def get_notices(
    category: Optional[str] = Query(None, description="카테고리 필터 (예: 학사, 장학, 청년정책)"),
    keyword: Optional[str] = Query(None, description="제목 또는 키워드 검색어"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수")
):
    """
    저장된 공지사항 목록을 조회합니다. 카테고리 필터링 및 검색어 검색을 지원합니다.
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("notices").select("*").order("created_at", desc=True)

        if category:
            query = query.eq("category", category)

        response = query.limit(limit).execute()
        data = response.data or []

        # 키워드 검색어 매칭 (파이썬 메모리 단 필터링)
        if keyword:
            kw = keyword.strip().lower()
            filtered_data = []
            for item in data:
                title_match = kw in item.get("title", "").lower()
                tags_match = any(kw in tag.lower() for tag in item.get("keywords", []))
                if title_match or tags_match:
                    filtered_data.append(item)
            return {"total": len(filtered_data), "notices": filtered_data}

        return {"total": len(data), "notices": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"공지사항 조회 중 오류 발생: {str(e)}")


@app.post("/users/register", summary="사용자 알림 설정 등록/수정")
def register_user(user_req: UserRegisterRequest):
    """
    사용자의 이메일과 관심 키워드를 등록하거나 기존 설정을 수정합니다.
    """
    try:
        supabase = get_supabase_client()
        email = user_req.email.strip()
        cleaned_keywords = [k.strip() for k in user_req.keywords if k.strip()]

        # 기존 회원 확인
        existing = supabase.table("users").select("*").eq("email", email).execute()

        if existing.data:
            # 기존 사용자 설정 업데이트
            update_res = supabase.table("users").update({
                "keywords": cleaned_keywords,
                "is_active": True
            }).eq("email", email).execute()
            return {"message": "사용자 맞춤 알림 키워드가 성공적으로 수정되었습니다.", "data": update_res.data}
        else:
            # 신규 사용자 등록
            insert_res = supabase.table("users").insert({
                "email": email,
                "keywords": cleaned_keywords,
                "is_active": True
            }).execute()
            return {"message": "신규 알림 사용자로 성공적으로 등록되었습니다.", "data": insert_res.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 등록 중 오류 발생: {str(e)}")


@app.post("/pipeline/trigger", summary="수집 파이프라인 수시 실행 (관리자용)")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    스케줄러 주기와 상관없이 수집 및 요약/알림 파이프라인을 비동기로 수시 즉시 실행합니다.
    """
    background_tasks.add_task(run_daily_pipeline)
    return {"message": "Daily 수집 파이프라인 작업이 백그라운드에서 즉시 시작되었습니다."}


if __name__ == "__main__":
    # reload 옵션을 제거하여 스레드 signal 에러를 방지합니다.
    uvicorn.run("main:app", host="127.0.0.1", port=8000)