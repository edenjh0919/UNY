import os
from datetime import datetime, date
import streamlit as st
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# 모듈 안전 임포트 (파일이 없거나 오류 발생 시 기본 동작 fallback 처리)
# ------------------------------------------------------------------------------
try:
    from database import get_supabase_client
except ModuleNotFoundError:
    def get_supabase_client():
        return None

try:
    from crawler import parse_sample_notice_list, fetch_notice_content
except ModuleNotFoundError:
    parse_sample_notice_list = None
    fetch_notice_content = None

try:
    from llm_summarizer import summarize_notice
except ModuleNotFoundError:
    def summarize_notice(text):
        return text[:100] + "..." if text else "요약 내용이 없습니다."

# ------------------------------------------------------------------------------
# 1. 페이지 및 CSS 기본 스타일 설정
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="UNY",
    page_icon="🎓",
    layout="wide"
)

# 커스텀 CSS 스타일 적용
st.markdown("""
<style>
    .main { background-color: #ffffff; }
    
    /* 상단 환영 박스 */
    .welcome-box {
        background-color: #EBF3FE;
        border: 1.5px solid #2B2D42;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .welcome-title { font-size: 18px; font-weight: 600; color: #1E1E1E; margin-bottom: 4px; }
    .welcome-sub { font-size: 16px; font-weight: 700; color: #1E1E1E; }
    
    /* 공지 카드 스타일 */
    .notice-card {
        border: 1.5px solid #2B2D42;
        border-radius: 16px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 10px;
        background-color: #ffffff;
    }
    .badge-category {
        background-color: #E2E8F0;
        color: #4A5568;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .notice-title { font-size: 18px; font-weight: 800; color: #1A202C; margin-bottom: 2px; }
    .notice-subtitle { font-size: 13px; color: #4A5568; margin-bottom: 12px; font-weight: 600; }
    
    /* 요약문 박스 */
    .summary-box {
        background-color: #EBF5FF;
        border-radius: 10px;
        padding: 16px;
        min-height: 80px;
        margin-bottom: 12px;
        font-size: 14px;
        color: #2D3748;
        white-space: pre-line;
    }
    
    /* 키워드 태그 */
    .tag-item {
        background-color: #EDF2F7;
        color: #2D3748;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    
    /* 하단 통계 지표 박스 */
    .stat-card {
        background-color: #E2E8F0;
        border: 2px solid #1A202C;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
    }
    .stat-label { font-size: 15px; font-weight: 600; color: #2D3748; margin-bottom: 6px; }
    .stat-value { font-size: 22px; font-weight: 900; color: #000000; }
</style>
""", unsafe_allow_html=True)

load_dotenv()

@st.cache_resource
def init_db():
    try:
        return get_supabase_client()
    except Exception as e:
        return None

supabase = init_db()

# 세션 상태 초기화
if "user" not in st.session_state:
    st.session_state["user"] = None

# ------------------------------------------------------------------------------
# 2. 로그인 / 회원가입 화면 (비로그인 상태)
# ------------------------------------------------------------------------------
if not st.session_state["user"]:
    st.markdown("<h2 style='text-align: center;'>🎓 UNY</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>서비스를 이용하시려면 로그인해주세요.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
        
        # [탭 1] 로그인
        with tab_login:
            with st.form("login_form"):
                login_email = st.text_input("이메일 주소", placeholder="example@email.com")
                login_password = st.text_input("비밀번호", type="password")
                btn_login = st.form_submit_button("로그인", use_container_width=True)
                
                if btn_login:
                    clean_login_email = login_email.strip().lower()
                    clean_login_password = login_password.strip()

                    if not clean_login_email or not clean_login_password:
                        st.warning("이메일과 비밀번호를 모두 입력해주세요.")
                    elif supabase:
                        try:
                            res = supabase.table("users").select("*").eq("email", clean_login_email).execute()
                            if res.data:
                                user_data = res.data[0]
                                if user_data.get("password") == clean_login_password:
                                    st.session_state["user"] = user_data
                                    st.success("로그인 성공!")
                                    st.rerun()
                                else:
                                    st.error("비밀번호가 일치하지 않습니다.")
                            else:
                                st.error("등록되지 않은 이메일입니다.")
                        except Exception as e:
                            st.error(f"로그인 처리 오류: {e}")
                    else:
                        st.error("DB에 연결할 수 없습니다. .env 환경변수를 확인해주세요.")
        
        # [탭 2] 회원가입
        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("이메일 주소", placeholder="example@email.com")
                new_password = st.text_input("비밀번호", type="password")
                new_keywords = st.text_input("관심 키워드 (쉼표 구분)", placeholder="장학금, 인턴, 청년지원금")
                btn_signup = st.form_submit_button("회원가입 완료", use_container_width=True)
                
                if btn_signup:
                    clean_new_email = new_email.strip().lower()
                    clean_new_password = new_password.strip()

                    if not clean_new_email or "@" not in clean_new_email:
                        st.warning("올바른 이메일 주소를 입력해주세요.")
                    elif not clean_new_password:
                        st.warning("비밀번호를 입력해주세요.")
                    elif supabase:
                        try:
                            exist = supabase.table("users").select("id").eq("email", clean_new_email).execute()
                            if exist.data:
                                st.warning("이미 가입된 이메일입니다.")
                            else:
                                kw_list = list(set([k.strip() for k in new_keywords.split(",") if k.strip()]))
                                new_user = {
                                    "email": clean_new_email,
                                    "password": clean_new_password,
                                    "keywords": kw_list
                                }
                                supabase.table("users").insert(new_user).execute()
                                st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인 해주세요.")
                        except Exception as e:
                            st.error(f"회원가입 처리 오류: {e}")

# ------------------------------------------------------------------------------
# 3. 대시보드 화면 (로그인 완료 상태)
# ------------------------------------------------------------------------------
else:
    current_user = st.session_state["user"]
    user_email = current_user.get("email", "사용자")
    user_keywords = current_user.get("keywords", [])

    # 사이드바
    with st.sidebar:
        col_logo1, col_logo2 = st.columns([1, 3])
        with col_logo1:
            st.write("🎓")
        with col_logo2:
            st.markdown("<h2 style='margin:0; padding:0;'>UNY</h2>", unsafe_allow_html=True)
        
        st.caption(f"👤 {user_email}")
        st.markdown("---")
        
        menu = st.radio(
            "Navigation",
            ["🏠  Home/대시보드", "⭐  관심 키워드 관리", "✉️  이메일 알림 설정", "👤  마이페이지"],
            label_visibility="collapsed"
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪  로그아웃", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

    # 통계 계산
    today_str = date.today().isoformat()
    today_collected_count = 0
    keyword_matched_count = 0
    notifications_sent_count = 0

    if supabase:
        try:
            res_today = supabase.table("notices").select("*").gte("created_at", today_str).execute()
            today_notices = res_today.data or []
            today_collected_count = len(today_notices)

            if today_collected_count == 0:
                res_all = supabase.table("notices").select("*").limit(30).execute()
                today_notices = res_all.data or []
                today_collected_count = len(today_notices)

            for n in today_notices:
                notice_tags = n.get("keywords", [])
                notice_title = n.get("title", "")
                if any(kw.lower() in notice_title.lower() or kw in notice_tags for kw in user_keywords):
                    keyword_matched_count += 1

            notifications_sent_count = keyword_matched_count
        except Exception:
            today_collected_count = 0
            keyword_matched_count = 0
            notifications_sent_count = 0

    # --------------------------------------------------------------------------
    # [메뉴 1] Home / 대시보드
    # --------------------------------------------------------------------------
    if "Home/대시보드" in menu:
        user_name = user_email.split('@')[0]
        st.markdown(f"""
            <div class="welcome-box">
                <div class="welcome-title">안녕하세요, {user_name}님!</div>
                <div class="welcome-sub">🎓 오늘 맞춤 공지 {keyword_matched_count}건 도착하였습니다!</div>
            </div>
        """, unsafe_allow_html=True)

        category_list = ["학사공지", "장학금", "인턴/채용", "청년지원금", "전체"]
        selected_category = st.pills("카테고리 선택", category_list, default="장학금", label_visibility="collapsed")

        notices = []
        if supabase:
            try:
                query = supabase.table("notices").select("*").order("created_at", desc=True)
                if selected_category and selected_category != "전체":
                    query = query.eq("category", selected_category)
                res = query.limit(5).execute()
                notices = res.data or []
            except Exception:
                pass

        if not notices:
            notices = [{
                "category": selected_category if selected_category else "장학금",
                "title": "2026 하반기 교내 장학금 신청 안내",
                "site_name": "00대학교 교내 장학팀",
                "summary_3lines": "1. 2026학년도 하반기 교내 성적 및 복지 장학금 신청을 접수합니다.\n2. 신청 기한은 오는 10월 15일까지입니다.\n3. 종합정보시스템을 통해 온라인 신청이 가능합니다.",
                "keywords": ["학사공지", "장학금", "청년지원금"],
                "url": "https://example.com"
            }]

        for idx, notice in enumerate(notices):
            cat = notice.get("category", "장학금")
            title = notice.get("title", "공지사항 제목")
            site = notice.get("site_name", "출처 미상")
            summary = notice.get("summary_3lines", "요약 내용이 없습니다.")
            tags = notice.get("keywords", ["장학금", "학사공지"])
            url = notice.get("url", "#")

            tags_html = "".join([f'<span class="tag-item">{t}</span>' for t in tags])
            
            st.markdown(f"""
                <div class="notice-card">
                    <span class="badge-category">{cat}</span>
                    <div class="notice-title">{title}</div>
                    <div class="notice-subtitle">{site}</div>
                    <div class="summary-box">{summary}</div>
                    <div>{tags_html}</div>
                </div>
            """, unsafe_allow_html=True)
            
            col_btn1, col_btn2, col_empty = st.columns([1.5, 1.8, 4])
            with col_btn1:
                st.link_button("원문 보러가기 ↗", url, use_container_width=True)
            with col_btn2:
                if st.button("관심 키워드 등록", key=f"kw_btn_{idx}_{title}", use_container_width=True):
                    updated_kws = list(set(user_keywords + tags))
                    st.session_state["user"]["keywords"] = updated_kws
                    if supabase:
                        try:
                            supabase.table("users").update({"keywords": updated_kws}).eq("email", user_email).execute()
                        except Exception as e:
                            st.error(f"키워드 저장 중 오류가 발생했습니다: {e}")
                    st.toast("해당 공지의 태그가 관심 키워드에 추가되었습니다!")

        st.markdown("<br>", unsafe_allow_html=True)

        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">오늘 수집</div>
                    <div class="stat-value">({today_collected_count}건)</div>
                </div>
            """, unsafe_allow_html=True)

        with col_stat2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">키워드 매칭</div>
                    <div class="stat-value">({keyword_matched_count}건)</div>
                </div>
            """, unsafe_allow_html=True)

        with col_stat3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">알림 발송</div>
                    <div class="stat-value">({notifications_sent_count}건)</div>
                </div>
            """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # [메뉴 2] 관심 키워드 관리
    # --------------------------------------------------------------------------
    elif "관심 키워드 관리" in menu:
        st.title("⭐ 관심 키워드 관리")
        st.write("현재 등록된 관심 키워드 목록입니다.")
        
        if user_keywords:
            st.subheader("등록된 키워드 (클릭하여 삭제)")
            kw_cols = st.columns(min(len(user_keywords), 6))
            for i, kw in enumerate(user_keywords):
                with kw_cols[i % 6]:
                    if st.button(f"❌ {kw}", key=f"del_kw_{kw}"):
                        user_keywords.remove(kw)
                        st.session_state["user"]["keywords"] = user_keywords
                        if supabase:
                            try:
                                supabase.table("users").update({"keywords": user_keywords}).eq("email", user_email).execute()
                            except Exception as e:
                                st.error(f"삭제 중 오류: {e}")
                        st.toast(f"'{kw}' 키워드가 삭제되었습니다.")
                        st.rerun()
        else:
            st.info("등록된 키워드가 없습니다.")
        
        st.markdown("---")
        with st.form("keyword_form"):
            new_kw = st.text_input("새 키워드 추가 (쉼표로 구분)", placeholder="알바, 봉사활동, 공모전")
            btn_update_kw = st.form_submit_button("키워드 추가")
            
            if btn_update_kw:
                added_kws = [k.strip() for k in new_kw.split(",") if k.strip()]
                if added_kws:
                    updated_kws = list(set(user_keywords + added_kws))
                    if supabase:
                        try:
                            supabase.table("users").update({"keywords": updated_kws}).eq("email", user_email).execute()
                        except Exception as e:
                            st.error(f"업데이트 오류: {e}")
                    st.session_state["user"]["keywords"] = updated_kws
                    st.success("관심 키워드가 성공적으로 추가되었습니다!")
                    st.rerun()
                else:
                    st.warning("추가할 키워드를 입력해주세요.")

    # --------------------------------------------------------------------------
    # [메뉴 3] 이메일 알림 설정
    # --------------------------------------------------------------------------
    elif "이메일 알림 설정" in menu:
        st.title("✉️ 이메일 알림 설정")
        st.write(f"현재 알림 수신 이메일: **{user_email}**")
        st.toggle("이메일 알림 활성화", value=True)

    # --------------------------------------------------------------------------
    # [메뉴 4] 마이페이지
    # --------------------------------------------------------------------------
    elif "마이페이지" in menu:
        st.title("👤 마이페이지")
        st.subheader("계정 정보")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.text_input("이메일 주소", value=user_email, disabled=True)
        with col_info2:
            st.text_area("등록된 관심 키워드", value=", ".join(user_keywords) if user_keywords else "없음", disabled=True)
            
        st.markdown("---")
        with st.expander("🛠 세션 프로필 데이터"):
            safe_user_data = {k: v for k, v in current_user.items() if k != "password"}
            st.json(safe_user_data)