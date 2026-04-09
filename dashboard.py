import streamlit as st
import pandas as pd
from jira import JIRA
import gitlab
import re

# ==========================================
# 1. 설정값 (환경 변수(Secrets)를 통해 안전하게 불러오기)
# ==========================================

JIRA_SERVER = 'https://your-company.atlassian.net/'
GITLAB_SERVER = 'https://gitlab.your-company.com'

# 프로젝트 ID와 키도 임의의 값으로 변경 (실행할 땐 secrets.toml에서 진짜 값을 불러오게끔 응용)
TARGET_PROJECT_KEY = 'YOUR_PROJECT_KEY' 
GITLAB_PROJECT_ID = '123'               

# ==========================================
# 2. 데이터 수집 & 정렬 로직
# ==========================================
@st.cache_resource
def init_clients():
    # 비밀번호와 토큰은 st.secrets를 통해 로컬의 secrets.toml 파일에서만 안전하게 읽어옴
    jira = JIRA(server=JIRA_SERVER, basic_auth=(st.secrets["JIRA_EMAIL"], st.secrets["JIRA_TOKEN"]))
    gl = gitlab.Gitlab(GITLAB_SERVER, private_token=st.secrets["GITLAB_TOKEN"])
    return jira, gl.projects.get(GITLAB_PROJECT_ID)

@st.cache_data(ttl=600)
def get_all_jira_versions():
    jira, _ = init_clients()
    versions = jira.project_versions(TARGET_PROJECT_KEY)
    return [v.name for v in versions]

def version_sort_key(version_str):
    # 정규표현식으로 버전 문자열에서 숫자(a.b.c)만 추출하여 수학적으로 정렬 (예: 8.24.0)
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return [int(x) for x in match.groups()] 
    return [0, 0, 0] 

@st.cache_data(ttl=300)
def fetch_release_data(release_version):
    jira, project = init_clients()
    jql_query = f'project = "{TARGET_PROJECT_KEY}" AND fixVersion = "{release_version}" AND status NOT IN ("Done", "완료", "Closed")'
    issues = jira.search_issues(jql_query)
    
    all_tickets = []
    for issue in issues:
        ticket_key = issue.key           
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "미정"
        summary = issue.fields.summary   
        
        mrs = project.mergerequests.list(search=ticket_key, state='all')
        
        if not mrs:
            mr_status = "MR 없음 👻"
            pipeline_status = "-"
            mr_url = None
        else:
            mr = mrs[0] 
            mr_url = mr.web_url
            if mr.state == 'merged':
                mr_status = "머지 완료 ✅"
                pipeline_status = "성공"
            else:
                mr_status = "열려있음 🚨"
                pipelines = project.pipelines.list(ref=mr.source_branch, per_page=1)
                if pipelines:
                    pipeline_status = "성공 ✅" if pipelines[0].status == 'success' else f"{pipelines[0].status} ⏳"
                else:
                    pipeline_status = "파이프라인 없음"

        all_tickets.append({
            "담당자": assignee,
            "티켓": ticket_key,
            "작업명": summary,
            "연동 상태": mr_status,
            "빌드(바이너리)": pipeline_status,
            "MR 링크": mr_url
        })
    return all_tickets

# ==========================================
# 3. 대시보드 UI 그리기
# ==========================================
st.set_page_config(page_title="Release Merge Tracker", page_icon="🎯", layout="wide")
st.title("🎯 릴리즈 머지 & 연동 현황 대시보드")

st.sidebar.header("🔍 검색 필터")

all_versions = get_all_jira_versions()

selected_platform = st.sidebar.radio(
    "📱 플랫폼을 선택하세요", 
    ["iOS", "Android", "AndroidTV"],
    horizontal=True
)

platform_filtered_versions = [v for v in all_versions if selected_platform in v]
sorted_versions = sorted(platform_filtered_versions, key=version_sort_key, reverse=True)

if not sorted_versions:
    st.sidebar.warning(f"선택한 {selected_platform} 플랫폼의 버전이 존재하지 않습니다.")
    selected_version = None
else:
    selected_version = st.sidebar.selectbox(
        "🎯 조회할 버전을 선택하세요", 
        options=sorted_versions,
        index=0 
    )

st.sidebar.markdown("---")

if selected_version:
    if st.button("🔄 데이터 불러오기"):
        with st.spinner(f'{selected_version} 데이터를 분석 중입니다...'):
            results = fetch_release_data(selected_version)
            
            if not results:
                st.success("🎉 Jira에 남은 작업이 없습니다! (모두 Done 처리됨)")
            else:
                df = pd.DataFrame(results)
                
                total_cnt = len(df)
                unmerged_cnt = len(df[df["연동 상태"] == "열려있음 🚨"])
                no_mr_cnt = len(df[df["연동 상태"] == "MR 없음 👻"])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("총 남은 티켓", f"{total_cnt}개")
                col2.metric("바이너리 O, 머지 안함", f"{unmerged_cnt}개", delta="-문의 필요" if unmerged_cnt > 0 else "완벽", delta_color="inverse")
                col3.metric("MR조차 안 올림", f"{no_mr_cnt}개", delta="-확인 필요" if no_mr_cnt > 0 else "완벽", delta_color="inverse")
                
                st.markdown("---")
                
                tab1, tab2 = st.tabs(["🚨 문의 대상자 (머지 누락)", "📋 전체 티켓 연동 내역"])
                
                with tab1:
                    st.subheader("바이너리 O, 머지 X 상태 ")
                    target_df = df[(df["연동 상태"] == "열려있음 🚨") & (df["빌드(바이너리)"] == "성공 ✅")]
                    if target_df.empty:
                        st.write("해당하는 티켓이 없습니다. 평화롭네요! 🕊️")
                    else:
                        st.dataframe(target_df, column_config={"MR 링크": st.column_config.LinkColumn("바로가기")}, use_container_width=True, hide_index=True)
                
                with tab2:
                    st.subheader("현재 릴리즈 전체 티켓 상태")
                    st.dataframe(df, column_config={"MR 링크": st.column_config.LinkColumn("바로가기")}, use_container_width=True, hide_index=True)