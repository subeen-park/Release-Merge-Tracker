# Release Merge Tracker Dashboard

> **Jira와 GitLab API를 연동하여 릴리즈 버전별 머지(Merge) 누락을 실시간으로 추적하는 자동화 대시보드입니다.**

이 프로젝트는 릴리즈 일정 관리 과정에서 발생하는 반복적인 수동 확인 절차를 자동화하고, 빌드는 완료되었으나 머지가 누락되어 발생하는 배포 사고를 방지하기 위해 개발되었습니다.

---

## 1. 기획 배경 
* **기존 문제점:** 매주 릴리즈 시 수십 개의 티켓 상태(Jira)와 실제 코드 반영 여부(GitLab)를 PM이 일일이 수동으로 대조해야 했습니다.
* **리스크:** '빌드 성공' 메시지만 확인하고 코드 머지를 잊는 '휴먼 에러'가 발생할 경우, QA 서버에는 반영되었으나 운영 환경에는 기능이 누락되는 심각한 배포 사고로 이어질 수 있습니다.
* **해결 아이디어:** Jira의 버전 정보와 GitLab의 MR(Merge Request) 상태 및 파이프라인 결과를 API로 결합하여, 한눈에 '지각생'을 찾아내는 실시간 대시보드를 구축합니다.

## 2. 주요 기능 
* **플랫폼별 실시간 필터링:** iOS, Android, AndroidTV 등 플랫폼별 타겟 버전을 사이드바에서 즉시 검색 및 선택 가능.
* **지능형 버전 정렬:** 문자열 사전순이 아닌, Semantic Versioning(a.b.c) 기준의 수학적 정렬을 통해 항상 최신 릴리즈가 최상단에 노출.
* **상태별 교차 검증:**
    * `머지 완료 `: 코드 반영 및 빌드 성공 확인.
    * `열려있음 `: 빌드는 성공했으나 아직 머지하지 않은 '독촉 대상'.
    * `MR 없음 `: 개발은 완료(Jira 상태 기준)되었으나 코드 요청 자체가 없는 상태.
* **대시보드 메트릭:** 총 티켓 수, 독촉 필요 건수 등을 상단 지표(Metric)로 시각화하여 현황 파악 속도 극대화.

## 3. 기술 스택 (Tech Stack)
* **Language:** Python 3.x
* **Frontend:** Streamlit (Web Dashboard Framework)
* **Integrations:** Jira Software SDK, GitLab REST API
* **Data Handling:** Pandas (Dataframe Processing), Regex (Version Sorting)

## 4. 성과 및 임팩트 (Impact)
* **시간 단축:** 기존 릴리즈 전 전수 조사 시간 **약 30분 -> 30초**로 획기적 단축 (약 60배 효율화).
* **보안 및 정확성:** 수동 체크로 인한 휴먼 에러 발생 가능성을 0%로 차단.
* **커뮤니케이션 비용 감소:** 개발팀에게 일일이 물어볼 필요 없이 PM이 대시보드 링크 하나로 현황을 실시간 파악하고 즉각적인 Action Item 도출 가능.

---

## ⚙️ 설치 및 실행 방법 (Installation)

1.  **Repository Clone**
    ```bash
    git clone [https://github.com/subeen-park/Release-Merge-Tracker.git](https://github.com/subeen-park/Release-Merge-Tracker.git)
    cd Release-Merge-Tracker
    ```

2.  **필수 라이브러리 설치**
    ```bash
    pip install streamlit pandas jira-python python-gitlab
    ```

3.  **환경 설정 (Secrets)**
    `.streamlit/secrets.toml` 파일을 생성하고 아래 정보를 입력합니다. (해당 파일은 보안을 위해 `.gitignore`에 등록되어 있습니다.)
    ```toml
    JIRA_EMAIL = "your-email@example.com"
    JIRA_TOKEN = "your-jira-api-token"
    GITLAB_TOKEN = "your-gitlab-access-token"
    ```

4.  **대시보드 실행**
    ```bash
    streamlit run dashboard.py
    ```
