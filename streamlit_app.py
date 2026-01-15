import streamlit as st
import pandas as pd
import datetime
import uuid
import time

# 페이지 설정
st.set_page_config(page_title="밥상매치 2026", layout="wide", page_icon="🍚")

# 데이터 초기화 (없으면 생성)
if 'requests' not in st.session_state: st.session_state.requests = []
if 'bids' not in st.session_state: st.session_state.bids = []
if 'matches' not in st.session_state: st.session_state.matches = []

# --- 기능 함수 ---
def generate_auto_bid(req_id, owner_name, vacancy_rate):
    offer = "20% 할인 + 특수부위" if vacancy_rate >= 0.7 else "음료수 1병 서비스"
    tag = "🔥파격제안" if vacancy_rate >= 0.7 else "일반제안"
    return {
        "bid_id": str(uuid.uuid4())[:8],
        "req_id": req_id,
        "owner_name": owner_name,
        "offer": offer,
        "tag": tag,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    }

# --- 사이드바 ---
with st.sidebar:
    st.header("🍚 밥상매치 MVP")
    role = st.radio("역할 선택", ["👨‍👩‍👧‍👦 손님 (User)", "👨‍🍳 사장님 (Owner)", "📊 관리자 (Admin)"])
    st.divider()
    if st.button("🔄 새로고침 (반응 확인)"):
        st.rerun()

# --- 1. 손님 화면 ---
if role == "👨‍👩‍👧‍👦 손님 (User)":
    st.title("오늘 뭐 드시나요?")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1: loc = st.text_input("위치", "해운대")
        with c2: pp = st.number_input("인원", 1, 10, 4)
        with c3: menu = st.selectbox("메뉴", ["회", "고기", "한식"])
        
        if st.button("📢 사장님 호출하기", type="primary", use_container_width=True):
            st.session_state.requests.append({
                "id": str(uuid.uuid4())[:8],
                "location": loc, "people": pp, "menu": menu,
                "status": "입찰대기",
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            })
            st.toast("📡 호출 전송 완료!"); time.sleep(1); st.rerun()

    # 내 요청 현황
    if st.session_state.requests:
        my_req = st.session_state.requests[-1]
        st.info(f"내 요청 상태: {my_req['status']}")
        
        # 도착한 제안
        my_bids = [b for b in st.session_state.bids if b['req_id'] == my_req['id']]
        for b in my_bids:
            with st.container(border=True):
                st.write(f"🎁 **{b['owner_name']}**: {b['offer']}")
                if st.button("수락", key=b['bid_id']):
                    st.session_state.matches.append(b)
                    my_req['status'] = "매칭완료"
                    st.balloons(); st.success("예약 확정!"); st.rerun()

# --- 2. 사장님 화면 ---
elif role == "👨‍🍳 사장님 (Owner)":
    st.title("사장님 알림판")
    vacancy = st.slider("빈자리 비율 (높을수록 파격제안)", 0.0, 1.0, 0.8)
    
    # 대기 중인 호출
    reqs = [r for r in st.session_state.requests if r['status'] == "입찰대기"]
    if reqs:
        for r in reqs:
            with st.container(border=True):
                st.write(f"🔔 **{r['menu']} {r['people']}명** ({r['location']})")
                if st.button("⚡ 빈자리 채우기", key=f"btn_{r['id']}"):
                    st.session_state.bids.append(generate_auto_bid(r['id'], "내 가게", vacancy))
                    r['status'] = "제안도착"
                    st.toast("📨 제안 발송 완료!"); time.sleep(0.5); st.rerun()
    else:
        st.write("현재 대기 중인 호출이 없습니다.")
        
    # 매칭된 결과
    my_matches = [m for m in st.session_state.matches if m['owner_name'] == "내 가게"]
    if my_matches:
        st.divider()
        st.success(f"🎉 예약 확정 {len(my_matches)}건")
        st.dataframe(pd.DataFrame(my_matches)[['timestamp', 'offer']])

# --- 3. 관리자 화면 (CEO 대시보드) ---
elif role == "📊 관리자 (Admin)":
    st.title("📊 CEO 대시보드")
    st.markdown("---")
    
    # 1. 핵심 지표 (KPI) 계산
    total_matches = len(st.session_state.matches)
    total_requests = len(st.session_state.requests)
    # 가상의 객단가 (5만원) 적용하여 거래액 추산
    estimated_revenue = total_matches * 50000 
    
    # 2. 숫자판 (Metrics) 표시
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 누적 거래액 (GMV)", f"{estimated_revenue:,} 원", "실시간 집계")
    col2.metric("🤝 매칭 성사", f"{total_matches} 건", f"전체 요청 {total_requests}건 중")
    col3.metric("📉 평균 할인율", "18.5%", "사장님 설정 평균")

    st.markdown("---")

    # 3. 데이터가 있을 때만 그래프와 표 보여주기
    if st.session_state.matches:
        df_matches = pd.DataFrame(st.session_state.matches)
        
        # 보기 좋게 컬럼 정리
        display_df = df_matches[['timestamp', 'owner_name', 'offer', 'tag']]
        display_df.columns = ['체결시간', '가게명', '제공혜택', '구분']
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("📈 실시간 체결 현황")
            st.dataframe(display_df, use_container_width=True)
        with c2:
            st.subheader("🏆 인기 가게")
            st.bar_chart(df_matches['owner_name'].value_counts())
            
        # 엑셀 다운로드 버튼 (투자자 미팅용)
        csv = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 거래 장부 엑셀 다운로드",
            data=csv,
            file_name='babsang_revenue.csv',
            mime='text/csv',
        )
    else:
        st.info("아직 성사된 거래가 없습니다. 손님과 사장님 역할로 거래를 만들어보세요!")
