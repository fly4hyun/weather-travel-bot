###################################################################################################
###################################################################################################

# from datetime import datetime
import os

import streamlit as st

from utils.utils_streamlit_function import *
from utils.utils import get_dict_from_yaml

###################################################################################################

# current_date = datetime.now()

# now_date = current_date.strftime('%Y%m%d')
# now_time = current_date.strftime('%H:%M:%S')

###################################################################################################
###################################################################################################
### 어떤 유용한 기능을 제공 받을지 선택하는 페이지 (최종적으로는 선택말고 질문 하나로 해결할 예정)

def page_main():
    
    ###############################################################################################
    ### 체크박스
    
    st.markdown("-------------------------------------------")
    st.markdown("#")
    st.markdown("### Check The Service You Require")
    
    keywords = st.session_state.keywords.keys()
    
    keyword = st.radio(label = 'Check The Service You Require', options = keywords, label_visibility = 'hidden')
    st.session_state.selected_checkbox = keyword
    
    st.markdown("#")
    
    ###############################################################################################
    ### api 키 값 입력
    
    st.markdown("### Enter OpenAI API Key")
    st.session_state.openai_api_key = st.text_input("Enter OpenAI API Key", 
                                #value = "", 
                                value = '', 
                                key = "chatbot_api_key", 
                                type = "password", 
                                label_visibility="collapsed")
    
    ###############################################################################################
    
    st.markdown("#")
    Process = st.button("Process")

    ###############################################################################################
    ### 키 입력 및 체크박스 결과 확인 후 페이지 변수에 해당 페이지 값 할당
    
    if Process:
        if not st.session_state.openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()
        elif not st.session_state.selected_checkbox:
            st.info("Please check the box to continue.")
            st.stop()
        else:
            if 'population_density' == st.session_state.keywords[st.session_state.selected_checkbox][0]:
                st.info(" - 현재 개선 작업 진행 중 ...")
                st.stop()
                
            request_app_name = st.session_state.keywords[st.session_state.selected_checkbox][0]
            request_app_dict = get_dict_from_yaml("./yamls/templates/" + request_app_name + ".yaml")
            
            st.session_state.page = request_app_dict["page"][0]
            st.rerun()

###################################################################################################
###################################################################################################
### 문서 내 검색 페이지 정의 (질문 전에 메인 기능 동작)

def documents_page():
    
    ###############################################################################################
    ### 메인 메뉴
    
    with st.sidebar:
        
        st.markdown("## 빠른 시작")
        st.markdown("-------------------------------------------")
        Home_process = st.button("홈으로")
        reset_process = st.button("대화 내용 초기화")
        st.markdown("-------------------------------------------")
        #st.markdown("(새로운 날씨나 국내 여행 정보를 원하시면 내용을 초기화 해주세요.)")
    
    ### 홈으로 함수 동작
    if Home_process:
        home_reset_process()
    
    ### 대화 내용 초기화 함수 동작
    if reset_process:
        page_reset_process()
    
    ###############################################################################################
    ### 사전에 저장되어 있는 vector 값 호출
    
    ### 여러개 호출이 필요한 경우 (아직 기능 없음)
    # for request_app_name in st.session_state.keywords[st.session_state.selected_checkbox]:

    request_app_name = st.session_state.keywords[st.session_state.selected_checkbox][0]
    request_app_dict = get_dict_from_yaml("./yamls/templates/" + request_app_name + ".yaml")
    
    ### FAISS에서 vectordb 저장 시, 한글명으로 저장 안됨 -> mapping.yaml 파일로 폴더명, 파일명 숫자화
    documents_folder_path = os.path.join('sources', request_app_name)
    documents_list = os.listdir(documents_folder_path)
    
    if st.session_state.mapping_dict == None:
        if 'mapping.yaml' in documents_list:
            st.session_state.mapping_dict = get_dict_from_yaml(os.path.join(documents_folder_path, 'mapping.yaml'))

        if st.session_state.mapping_dict == None:
            st.session_state.mapping_dict = {}
    
    ###############################################################################################
    ### 새로운 문서 입력 시 해당 문서의 vector 값 저장

    with st.sidebar:
        save_file_embedding(documents_folder_path)
    
    ###############################################################################################
    ### 현재 저장되어 있는 문서 리스트 확인 및 삭제 기능
    
    with st.sidebar:
        file_list_expander(documents_folder_path, documents_list)

    ###############################################################################################
    ###############################################################################################
    ### 첫 질문 저장 및 출력

    header_dict = get_dict_from_yaml("./yamls/header.yaml")
    if st.session_state.keywords[st.session_state.selected_checkbox][0] in header_dict:
        for subheader in header_dict[st.session_state.keywords[st.session_state.selected_checkbox][0]]:
            st.subheader(subheader)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
                        
    ###############################################################################################
    ### 유저 질문 시작
    
    if user_question := st.chat_input("Please Enter Your Question: "):
        
        ###########################################################################################
        ### 저장되어 있는 vector 값 호출 및 llm 선언
        
        with st.spinner("Loading Document(s) ..."):
            if st.session_state.conversation == None:
                
                vectordb = load_vectordb_from_documents(documents_folder_path)
                if vectordb == None:
                    st.session_state.error_code = 'e0001'
                else:
                    st.session_state.conversation = get_conversation_chain(vectordb, st.session_state.openai_api_key)
                
        ###########################################################################################
        ### 유저 질문 messages 변수에 저장 및 출력
        
        st.session_state['current_query'] = user_question
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        with st.chat_message("user"):
            st.markdown(user_question)
            
        ###########################################################################################
        ### llm 답변 생성 및 출력
            
        response, source_documents = answer_question(user_question)
        
        ###########################################################################################
        
        ### 참조 문서 출력
        if 'reference' in request_app_dict:
            view_reference(source_documents)
        
            with st.spinner("Generating a Graph..."):
                ### 관련 문서 그래프로 출력
                if 'graph' in request_app_dict:
                    view_graph()
        
        ###########################################################################################
        ### llm 답변 messages 변수에 저장
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        print(st.session_state['messages'])
###################################################################################################
###################################################################################################
### api 페이지 정의 (질문 후 메인 기능 동작)

def api_page():
    
    ###############################################################################################
    ### 메인 메뉴
    
    with st.sidebar:
        
        st.markdown("## 빠른 시작")
        st.markdown("-------------------------------------------")
        Home_process = st.button("홈으로")
        reset_process = st.button("대화 내용 초기화")
        st.markdown("-------------------------------------------")
        st.markdown("(새로운 날씨나 국내 여행 정보를 원하시면 내용을 초기화 해주세요.)")
    
    ### 홈으로 함수 동작
    if Home_process:
        home_reset_process()

    ### 대화 내용 초기화 함수 동작
    if reset_process:
        page_reset_process()
    
    ###############################################################################################
    ###############################################################################################
    ### 첫 질문 저장 및 출력
    
    header_dict = get_dict_from_yaml("./yamls/header.yaml")
    if st.session_state.keywords[st.session_state.selected_checkbox][0] in header_dict:
        for subheader in header_dict[st.session_state.keywords[st.session_state.selected_checkbox][0]]:
            st.subheader(subheader)
            
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    ###############################################################################################
    ### 유저 질문 시작
    
    if question := st.chat_input("Please Enter Your Question: "):
        
        ###########################################################################################
        ### 해당 기능의 templates 값이 저장되어 있는 yaml 파일 호출
        
        ### 여러개 호출이 필요한 경우 (아직 기능 없음)
        # for request_app_name in st.session_state.keywords[st.session_state.selected_checkbox]:
        
        request_app_name = st.session_state.keywords[st.session_state.selected_checkbox][0]
        request_app_dict = get_dict_from_yaml("./yamls/templates/" + request_app_name + ".yaml")
        
        ###########################################################################################
        ### chat_history가 없으면 api 호출 및 llm 선언
        
        with st.spinner("Gathering API data ..."):
            if st.session_state.chat_history == None:
                for template_key in request_app_dict['templates']:
                    
                    llm_from_yaml(request_app_dict, template_key, question)

            st.session_state.result = None

        ###########################################################################################
        ### 유저 질문 messages 변수에 저장 및 출력
        
        st.session_state['current_query'] = question
        st.session_state.messages.append({"role": "user", "content": question})
        
        with st.chat_message("user"):
            st.markdown(question)
            
        ###########################################################################################
        ### llm 답변 생성 및 출력
        
        if 'stream' in request_app_dict:
            response, source_documents = answer_question(question, 1)
        else:
            response, source_documents = answer_question(question)

        ###########################################################################################
        ### llm 답변 messages 변수에 저장
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        print(st.session_state['messages'])
###################################################################################################
###################################################################################################
