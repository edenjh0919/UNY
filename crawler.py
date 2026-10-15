import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def parse_sample_notice_list() -> List[Dict]:
    """
    공지사항 리스트를 수집하는 샘플 크롤러 함수
    """
    # 기본 샘플 데이터 제공 (크롤링 연결 전 테스트용)
    sample_data = [
        {
            "category": "장학금",
            "title": "2026학년도 2학기 교내/외 장학금 신청 안내",
            "site_name": "학교 홈페이지",
            "url": "https://www.example.com/notice/1"
        },
        {
            "category": "학사공지",
            "title": "2026학년도 수강신청 및 성적 평가 기준 안내",
            "site_name": "학사지원팀",
            "url": "https://www.example.com/notice/2"
        }
    ]
    return sample_data

def fetch_notice_content(url: str) -> str:
    """
    공지사항 상세 페이지 본문을 긁어오는 함수
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text()
    except Exception as e:
        print(f"크롤링 오류 ({url}): {e}")
    return "본문 내용을 불러올 수 없습니다."