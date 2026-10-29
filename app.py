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
    .badge-category-red {
        background-color: #FF6B6B;
        color: #FFFFFF;
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

    /* 알림 드롭다운 카드 스타일 */
    .noti-item {
        border-bottom: 1px solid #edf2f7;
        padding: 10px 0;
    }
    .noti-item-urgent {
        background-color: #fff5f5;
        border-left: 3px solid #e53e3e;
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .noti-title {
        font-size: 13px;
        font-weight: bold;
        color: #2d3748;
    }
    .noti-desc {
        font-size: 12px;
        color: #4a5568;
        margin-top: 2px;
    }
    .noti-time {
        font-size: 11px;
        color: #a0aec0;
        margin-top: 4px;
    }

    /* 전체 알림 전용 카드 스타일 */
    .noti-page-card {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        background-color: #FFFFFF;
    }
    .noti-page-card-read {
        border: 1px solid #EDF2F7;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        background-color: #F7FAFC;
        opacity: 0.75;
    }
    .noti-page-card-urgent {
        border: 1.5px solid #FEB2B2;
        border-left: 5px solid #E53E3E;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        background-color: #FFF5F5;
    }

    /* 마이페이지 & 보관함 커스텀 스타일 */
    .profile-avatar {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background-color: #C4C4C4;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        color: #555555;
    }
    .profile-info-label {
        font-size: 16px;
        font-weight: 700;
        color: #1A202C;
        margin-bottom: 8px;
    }
    .profile-info-val {
        font-weight: 400;
        color: #4A5568;
    }
    .mypage-section-card {
        background-color: #F8F9FA;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .mypage-card-red-border {
        border: 1.5px solid #FF6B6B;
        border-radius: 16px;
        padding: 20px;
        background-color: #FFF5F5;
        margin-bottom: 12px;
    }
    .history-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #EDF2F7;
        font-size: 14px;
        color: #2D3748;
    }
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

# ------------------------------------------------------------------------------
# 세션 상태 초기화
# ------------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if "notifications" not in st.session_state:
    st.session_state["notifications"] = [
        {
            "id": 1,
            "is_urgent": True,
            "title": "[긴급] 학사일정 변경 안내",
            "desc": "[학사공지] 2026학년도 2학기 중간평가 일정이 변경되었습니다.",
            "time": "방금 전",
            "is_read": False
        },
        {
            "id": 2,
            "is_urgent": False,
            "title": "[장학금] 2026학년도 2학기 교내 성적 및 맞춤 복지장학금 신청이 시작되었습니다.",
            "desc": "신청 기한 내 구비서류를 확인 후 접수 바랍니다.",
            "time": "1시간 전",
            "is_read": False
        },
        {
            "id": 3,
            "is_urgent": False,
            "title": "[인턴/채용] 2026 디자인 크리에이션 챌린지 공모전 안내",
            "desc": "디자인 관련 공모전 참가자 모집.",
            "time": "3시간 전",
            "is_read": False
        }
    ]

if "show_new_notice_pop" not in st.session_state:
    st.session_state["show_new_notice_pop"] = True

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "🏠  Home/대시보드"

# 관심 공지 보관함 데이터
if "saved_notices" not in st.session_state:
    st.session_state["saved_notices"] = [
        {
            "id": 101,
            "category": "인턴/채용",
            "title": "2026 디자인 크리에이션 챌린지(DCC) 3D프린팅 제품디자인 공모전SPECIAL",
            "site_name": "단국대-스트라타시스 첨단제조융합연구센터",
            "summary": "1. 2026 디자인 크리에이션 챌린지(DCC) 3D프린팅 제품디자인 공모전SPECIAL\n2. 전국 대학생 대외활동 및 인턴십 공고입니다.\n3. 세부 일정 및 지원 자격은 원문 참조",
            "keywords": ["인턴", "대외활동", "채용", "공모전"],
            "url": "https://example.com"
        },
        {
            "id": 102,
            "category": "학사공지",
            "title": "[안산대학교] 2026학년도 2학기 중간평가 및 주요 학사일정 안내",
            "site_name": "안산대학교 학사지원팀",
            "summary": "1. 2026학년도 2학기 중간평가 일정 안내입니다.\n2. 세부 교과목 시험 일정은 학과 홈페이지 확인",
            "keywords": ["학사일정", "중간고사", "안산대"],
            "url": "https://example.com"
        }
    ]

# ------------------------------------------------------------------------------
# 신규 공지 팝업 모달 함수
# ------------------------------------------------------------------------------
@st.dialog("🔔 [UNY] 신규 공지 알림")
def show_new_notice_dialog(notice_title):
    st.write(f"**{notice_title}** 공지가 등록되었습니다.")
    if st.button("확인", use_container_width=True):
        st.session_state["show_new_notice_pop"] = False
        st.rerun()

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
                
                # 학교 선택 드롭다운 추가 (필요에 따라 목록 추가/수정 가능)
                school_options = ["안산대학교", "단국대학교", "가천대학교", "한양대학교", "기타 (직접 입력)"]
                selected_school = st.selectbox("학교 선택", school_options)
                
                # '기타' 선택 시 직접 입력받을 필드
                custom_school = ""
                if selected_school == "기타 (직접 입력)":
                    custom_school = st.text_input("학교 이름을 직접 입력해주세요", placeholder="예: 서울대학교")
                
                new_dept = st.text_input("학과 입력", placeholder="예: 컴퓨터공학과")
                new_keywords = st.text_input("관심 키워드 (쉼표 구분)", placeholder="장학금, 인턴, 청년지원금")
                
                btn_signup = st.form_submit_button("회원가입 완료", use_container_width=True)
                
                if btn_signup:
                    clean_new_email = new_email.strip().lower()
                    clean_new_password = new_password.strip()
                    
                    # 최종 저장할 학교명 결정
                    final_school = custom_school.strip() if selected_school == "기타 (직접 입력)" else selected_school

                    if not clean_new_email or "@" not in clean_new_email:
                        st.warning("올바른 이메일 주소를 입력해주세요.")
                    elif not clean_new_password:
                        st.warning("비밀번호를 입력해주세요.")
                    elif selected_school == "기타 (직접 입력)" and not final_school:
                        st.warning("학교 이름을 입력해주세요.")
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
                                    "university": final_school,  # school -> university 로 컬럼명 변경
                                    "department": new_dept.strip(),
                                    "keywords": kw_list
                                }
                                supabase.table("users").insert(new_user).execute()
                                st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인 해주세요.")
                        except Exception as e:
                            st.error(f"회원가입 처리 오류: {e}")

# ------------------------------------------------------------------------------
# 3. 대시보드 및 메인 앱 화면 (로그인 완료 상태)
# ------------------------------------------------------------------------------
else:
    current_user = st.session_state["user"]
    user_email = current_user.get("email", "yourim@ansan.ac.kr")
    user_name = current_user.get("name", "신유림")
    user_school = current_user.get("university", "안산대학교")  # school -> university 키값 변경
    user_dept = current_user.get("department", "컴퓨터공학과")
    user_keywords = current_user.get("keywords", ["장학금", "인턴", "청년지원금"])

    notifications = st.session_state.get("notifications", [])

    # 상단 벨 모양 알림 버튼
    unread_count = sum(1 for n in notifications if not n.get("is_read", False))
    bell_label = f"🔔 알림 ({unread_count})" if unread_count > 0 else "🔔 알림"

    top_col1, top_col2 = st.columns([8, 2])
    with top_col2:
        with st.popover(bell_label, use_container_width=True):
            sub_c1, sub_c2 = st.columns([1, 1])
            with sub_c1:
                st.markdown("### 알림")
            with sub_c2:
                if st.button("전체 읽음으로 표시", key="mark_all_read", use_container_width=True):
                    for n in notifications:
                        n["is_read"] = True
                    st.session_state["notifications"] = notifications
                    st.rerun()

            st.markdown("---")

            if not notifications:
                st.caption("새로운 알림이 없습니다.")
            else:
                for noti in notifications:
                    if noti.get("is_urgent", False):
                        st.markdown(f"""
                        <div class="noti-item-urgent">
                            <div class="noti-title" style="color:#c53030;">🚨 {noti['title']}</div>
                            <div class="noti-desc">{noti['desc']}</div>
                            <div class="noti-time">{noti['time']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="noti-item">
                            <div class="noti-title">🔔 {noti['title']}</div>
                            <div class="noti-desc">{noti['desc']}</div>
                            <div class="noti-time">{noti['time']}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            if st.button("모든 알림 보기", key="view_all_noti", use_container_width=True):
                st.session_state["nav_page"] = "🔔  전체 알림 목록"
                st.rerun()

    # 신규 공지 팝업 노출
    if st.session_state.get("show_new_notice_pop", False):
        show_new_notice_dialog("[장학금] 2026학년도 2학기 맞춤 장학금 신청")

    # 사이드바 (관심 공지 보관함 복구)
    menu_options = ["🏠  Home/대시보드", "❤️  관심 공지 보관함", "🔔  전체 알림 목록", "👤  마이페이지"]
    default_idx = menu_options.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in menu_options else 0

    with st.sidebar:
        col_logo1, col_logo2 = st.columns([1, 3])
        with col_logo1:
            st.write("🎓")
        with col_logo2:
            st.markdown("<h2 style='margin:0; padding:0;'>UNY</h2>", unsafe_allow_html=True)
        
        st.caption(f"👤 {user_name}님 ({user_school})")
        st.markdown("---")
        
        selected_menu = st.radio(
            "Navigation",
            menu_options,
            index=default_idx,
            label_visibility="collapsed"
        )
        st.session_state["nav_page"] = selected_menu
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪  로그아웃", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

    # 통계 계산
    today_str = date.today().isoformat()
    today_collected_count = 0
    notifications_sent_count = len(notifications)

    if supabase:
        try:
            res_today = supabase.table("notices").select("*").gte("created_at", today_str).execute()
            today_notices = res_today.data or []
            today_collected_count = len(today_notices)

            if today_collected_count == 0:
                res_all = supabase.table("notices").select("*").limit(30).execute()
                today_notices = res_all.data or []
                today_collected_count = len(today_notices)
        except Exception:
            today_collected_count = 0

    # --------------------------------------------------------------------------
    # [메뉴 1] Home / 대시보드
    # --------------------------------------------------------------------------
    if "Home/대시보드" in selected_menu:
        st.markdown(f"""
            <div class="welcome-box">
                <div class="welcome-title">안녕하세요, {user_name}님! ({user_school})</div>
                <div class="welcome-sub">🎓 오늘 도착한 맞춤 공지사항 및 축제/학사 일정을 확인하세요!</div>
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

            tags_html = "".join([f'<span class="tag-item">#{t}</span>' for t in tags])
            
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
                if st.button("❤️ 보관함 저장", key=f"save_btn_{idx}_{title}", use_container_width=True):
                    new_saved = {
                        "id": len(st.session_state["saved_notices"]) + 1,
                        "category": cat,
                        "title": title,
                        "site_name": site,
                        "summary": summary,
                        "keywords": tags,
                        "url": url
                    }
                    st.session_state["saved_notices"].append(new_saved)
                    st.toast("관심 공지 보관함에 저장되었습니다!")

        st.markdown("<br>", unsafe_allow_html=True)

        col_stat1, col_stat2 = st.columns(2)
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
                    <div class="stat-label">알림 발송</div>
                    <div class="stat-value">({notifications_sent_count}건)</div>
                </div>
            """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # [메뉴 2] 관심 공지 보관함 (하트 보관함 화면)
    # --------------------------------------------------------------------------
    elif "관심 공지 보관함" in selected_menu:
        st.markdown("<h1 style='font-size: 28px; font-weight: 800;'>❤️ 관심 공지 보관함</h1>", unsafe_allow_html=True)
        st.caption("저장해둔 맞춤 공지사항 목록입니다.")
        st.markdown("---")

        saved_notices = st.session_state.get("saved_notices", [])
        if not saved_notices:
            st.info("보관함에 저장된 관심 공지가 없습니다.")
        else:
            for s_idx, s_notice in enumerate(saved_notices):
                tags_html = "".join([f'<span class="tag-item">#{t}</span>' for t in s_notice['keywords']])
                
                st.markdown(f"""
                <div class="mypage-card-red-border">
                    <span class="badge-category-red">{s_notice['category']}</span>
                    <div style="font-size: 18px; font-weight: 800; color: #1A202C; margin-bottom: 4px;">{s_notice['title']}</div>
                    <div style="font-size: 13px; color: #4A5568; margin-bottom: 12px; font-weight: 600;">📍 {s_notice['site_name']}</div>
                    <div class="summary-box">{s_notice['summary']}</div>
                    <div>{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)

                sc1, sc2, _ = st.columns([1.5, 1.5, 5])
                with sc1:
                    st.link_button("원문 보러가기 ↗", s_notice['url'], use_container_width=True)
                with sc2:
                    if st.button("💔 하트 삭제", key=f"del_saved_page_{s_notice['id']}_{s_idx}", use_container_width=True):
                        saved_notices.pop(s_idx)
                        st.session_state["saved_notices"] = saved_notices
                        st.toast("관심 공지 보관함에서 삭제되었습니다.")
                        st.rerun()

    # --------------------------------------------------------------------------
    # [메뉴 3] 전체 알림 목록 페이지
    # --------------------------------------------------------------------------
    elif "전체 알림 목록" in selected_menu:
        st.title("🔔 전체 알림 목록")
        st.caption("수신된 모든 맞춤 공지 및 시스템 알림 내역입니다.")

        head_col1, head_col2 = st.columns([6, 2])
        with head_col1:
            st.write(f"총 **{len(notifications)}**개의 알림 (미확인 **{unread_count}**개)")
        with head_col2:
            if st.button("✓ 전체 읽음으로 표시", key="noti_page_read_all", use_container_width=True):
                for n in notifications:
                    n["is_read"] = True
                st.session_state["notifications"] = notifications
                st.rerun()

        st.markdown("---")

        if not notifications:
            st.info("도착한 알림이 없습니다.")
        else:
            for idx, noti in enumerate(notifications):
                is_read = noti.get("is_read", False)
                is_urgent = noti.get("is_urgent", False)
                
                if is_urgent:
                    card_class = "noti-page-card-urgent"
                    badge = "<span style='color:#E53E3E; font-weight:bold;'>[🚨 긴급]</span> "
                elif is_read:
                    card_class = "noti-page-card-read"
                    badge = "<span style='color:#718096;'>[읽음]</span> "
                else:
                    card_class = "noti-page-card"
                    badge = "<span style='color:#3182CE; font-weight:bold;'>[NEW]</span> "

                st.markdown(f"""
                <div class="{card_class}">
                    <div style="font-size: 16px; font-weight: 700; color: #2D3748; margin-bottom: 4px;">
                        {badge}{noti['title']}
                    </div>
                    <div style="font-size: 14px; color: #4A5568; margin-bottom: 8px;">
                        {noti['desc']}
                    </div>
                    <div style="font-size: 12px; color: #A0AEC0;">
                        🕒 {noti['time']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                btn_c1, btn_c2, _ = st.columns([1.5, 1.2, 5.3])
                with btn_c1:
                    read_btn_label = "읽음 해제" if is_read else "읽음 표시"
                    if st.button(read_btn_label, key=f"toggle_read_{noti['id']}_{idx}"):
                        notifications[idx]["is_read"] = not is_read
                        st.session_state["notifications"] = notifications
                        st.rerun()
                with btn_c2:
                    if st.button("삭제", key=f"del_noti_{noti['id']}_{idx}"):
                        notifications.pop(idx)
                        st.session_state["notifications"] = notifications
                        st.rerun()
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # [메뉴 4] 마이페이지
    # --------------------------------------------------------------------------
    elif "마이페이지" in selected_menu:
        st.markdown(f"<h1 style='font-size: 32px; font-weight: 800;'>안녕하세요, {user_name}님!</h1>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # 1. 프로필 영역
        prof_col1, prof_col2, prof_col3 = st.columns([1.2, 5, 0.5])
        with prof_col1:
            st.markdown("""
            <div class="profile-avatar">
                👤
            </div>
            """, unsafe_allow_html=True)
        with prof_col2:
            st.markdown(f"""
            <div style="line-height: 1.8;">
                <div class="profile-info-label">이름: <span class="profile-info-val">{user_name}</span></div>
                <div class="profile-info-label">이메일: <span class="profile-info-val">{user_email}</span></div>
                <div class="profile-info-label">학교: <span class="profile-info-val">{user_school}</span></div>
                <div class="profile-info-label">소속 학과: <span class="profile-info-val">{user_dept}</span></div>
            </div>
            """, unsafe_allow_html=True)
        with prof_col3:
            if st.button("✏️", key="edit_name"): st.toast("이름 수정")
            if st.button("✏️", key="edit_email"): st.toast("이메일 수정")
            if st.button("✏️", key="edit_university"): st.toast("학교 수정")
            if st.button("✏️", key="edit_dept"): st.toast("학과 수정")

        st.markdown("<br><br>", unsafe_allow_html=True)

        # 2. 관심 공지 보관함 (마이페이지 내 표시)
        st.markdown("<h3 style='font-size: 20px; font-weight: 800;'>❤️ 관심 공지 보관함</h3>", unsafe_allow_html=True)
        
        saved_notices = st.session_state.get("saved_notices", [])
        if not saved_notices:
            st.info("보관함에 저장된 관심 공지가 없습니다.")
        else:
            for s_idx, s_notice in enumerate(saved_notices):
                tags_html = "".join([f'<span class="tag-item">#{t}</span>' for t in s_notice['keywords']])
                
                st.markdown(f"""
                <div class="mypage-card-red-border">
                    <span class="badge-category-red">{s_notice['category']}</span>
                    <div style="font-size: 18px; font-weight: 800; color: #1A202C; margin-bottom: 4px;">{s_notice['title']}</div>
                    <div style="font-size: 13px; color: #4A5568; margin-bottom: 12px; font-weight: 600;">📍 {s_notice['site_name']}</div>
                    <div class="summary-box">{s_notice['summary']}</div>
                    <div>{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)

                sc1, sc2, _ = st.columns([1.5, 1.5, 5])
                with sc1:
                    st.link_button("원문 보러가기 ↗", s_notice['url'], use_container_width=True)
                with sc2:
                    if st.button("💔 하트 삭제", key=f"del_saved_my_{s_notice['id']}_{s_idx}", use_container_width=True):
                        saved_notices.pop(s_idx)
                        st.session_state["saved_notices"] = saved_notices
                        st.toast("관심 공지 보관함에서 삭제되었습니다.")
                        st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)

        # 3. 내 공지 수신 내역 & 알림 설정 영역
        col_hist, col_set = st.columns([6, 4])
        
        with col_hist:
            st.markdown("""
            <div class="mypage-section-card">
                <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 16px;">내 공지 수신 내역 (최근 30일)</h3>
                <div class="history-row">
                    <span>안산대 장학금 공지 - 2026.10.01</span>
                    <span style="color: #9F7AEA;">✉️ 수신</span>
                </div>
                <div class="history-row">
                    <span>안산대 인턴 채용 - 2026.09.28</span>
                    <span style="color: #ED64A6;">📢 수신</span>
                </div>
                <div class="history-row" style="border-bottom: none;">
                    <span>안산대 인턴 채용 - 2026.09.17</span>
                    <span style="color: #9F7AEA;">✉️ 수신</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_set:
            st.markdown("""
            <div class="mypage-section-card" style="min-height: 190px;">
                <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 16px;">알림 설정</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.toggle("키워드 알림", value=True, key="toggle_kw_noti")
            st.toggle("전체 공지 ON/OFF", value=False, key="toggle_all_noti")

        # 4. 회원정보 수정/탈퇴 버튼
        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns([7, 3])
        with btn_col2:
            if st.button("회원정보 수정/탈퇴", use_container_width=True, type="primary"):
                st.toast("회원정보 수정 및 탈퇴 화면으로 이동합니다.")