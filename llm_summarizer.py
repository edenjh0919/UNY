# llm_summarizer.py

def summarize_notice(content: str) -> str:
    """
    공지사항 본문을 수신하여 LLM으로 요약문(3줄)을 반환하는 함수 예시
    """
    if not content:
        return "본문 내용이 없습니다."
    
    # TODO: OpenAI API 또는 다른 LLM 호출 로직 작성 위치
    return content