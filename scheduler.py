# scheduler.py 예시 코드

def run_daily_pipeline():
    """
    크롤링, 요약 및 이메일 알림을 실행하는 일일 파이프라인 함수
    """
    print("🚀 수집 및 알림 파이프라인을 실행합니다...")
    
    # 예: 크롤링 -> DB 저장 -> 요약 -> 이메일 발송 실행 로직
    try:
        # 여기에 기존 파이프라인 로직 연결
        print("✅ 파이프라인 실행 완료!")
    except Exception as e:
        print(f"❌ 파이프라인 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    run_daily_pipeline()