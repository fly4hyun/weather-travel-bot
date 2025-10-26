###################################################################################################
###################################################################################################

import os

import streamlit as st

from utils.utils_streamlit_ui import page_main, documents_page, api_page
from utils.utils import get_dict_from_yaml

###################################################################################################

os.environ['OPENAI_API_KEY'] = '키 입력'

###################################################################################################
###################################################################################################

def main():
    
    ###############################################################################################
    ### 웹 페이지 레이아웃 설정
    
    st.set_page_config(
        page_title="DirChat", 
        page_icon=":books:"
        )

    st.title(':blue[Lifelog] 통합 :red[LLM] 서비스 :books:')
    
    ###############################################################################################
    ### st 전역 변수 선언 및 정의
    
    ### 현재 활성화된 페이지 저장 
    if "page" not in st.session_state:
        st.session_state.page = "main_page"
        
    ### openai api key 저장 변수
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = None
        
    ### 체크박스 키워드 변수 선언
    if "keywords" not in st.session_state:
        st.session_state.keywords = get_dict_from_yaml('./yamls/keywords.yaml')
        
    ### chatbot llm 모델 저장 변수
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
        
    ### chat history 저장 변수 - weather의 경우 아직 기록하는 기능은 없음
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
        
    # ### 
    # if "processComplete" not in st.session_state:
    #     st.session_state.processComplete = None
    
    ### 함수 끼리 결과를 공유하기 위한 변수 선언
    if "result" not in st.session_state:
        st.session_state.result = None
        
    # ### 
    # if "file_check" not in st.session_state:
    #     st.session_state.file_check = 'Done'
    
    ### 실행 오류에 관한 에러 코드 저장 변수
    if "error_code" not in st.session_state:
        st.session_state.error_code = None
        
    ### chatbot과 주고 받는 메세지 기록 변수
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [{"role": "assistant", 
                                    "content": "안녕하세요! 제가 알고 있는 내용에 대한 질문을 입력해주세요.."}]
    
    ### 체크박스 선택 결과 저장 변수
    if 'selected_checkbox' not in st.session_state:
        st.session_state.selected_checkbox = None
    
    ### 파일명과 임베딩 source 폴더 이름 간의 매핑 결과 저장 변수
    if 'mapping_dict' not in st.session_state:
        st.session_state.mapping_dict = None

    ### 함수간 prompt 결과를 공유하기 위한 변수
    if 'prompt' not in st.session_state:
        st.session_state.prompt = None
            
    ###############################################################################################
    ### 페이지 이동
    
    ### 시작 페이지
    if st.session_state.page == "main_page":
        page_main()
    
    ### 문서 내 검색 페이지
    if st.session_state.page == "documents_page":
        documents_page()
        
    ### api 호출 및 유용한 정보 출력 페이지 (현재는 날씨만 가능)
    if st.session_state.page == "api_page":
        api_page()

###################################################################################################
###################################################################################################

if __name__ == '__main__':
    main()

###################################################################################################
###################################################################################################