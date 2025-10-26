###################################################################################################
###################################################################################################

from datetime import datetime
import os
import shutil
import random
import yaml

from typing import Dict

import streamlit as st
import streamlit.components.v1 as components

from langchain_community.callbacks import get_openai_callback
from langchain.prompts.prompt import PromptTemplate

from pyvis.network import Network

from utils.utils_documents import *
from utils.utils_weather import *
from utils.utils_llm import *
from utils.utils import error_message, result_from_file

###################################################################################################
### 현재 시간 및 날짜 선언

current_date = datetime.now()

now_date = current_date.strftime('%Y%m%d')
now_time = current_date.strftime('%H:%M:%S')

###################################################################################################
###################################################################################################

# def select_checkbox(option):
#     st.session_state.selected_checkbox = option

###################################################################################################
### 메인 메뉴 동작 함수 (변수 초기화 후 페이지 이동)

def home_reset_process():
    
    st.session_state.page = "main_page"
    st.session_state.openai_api_key = None
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.result = None
    st.session_state.error_code = None
    st.session_state.mapping_dict = None
    st.session_state.messages = [{"role": "assistant", 
                                "content": "안녕하세요! 제가 알고 있는 내용에 대한 질문을 입력해주세요.."}]
    st.rerun()

def page_reset_process():

    #st.session_state.page = "QA_page"
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.result = None
    st.session_state.error_code = None
    st.session_state.mapping_dict = None
    
    st.session_state.messages = [{"role": "assistant", 
                                "content": "안녕하세요! 제가 알고 있는 내용에 대한 질문을 입력해주세요.."}]
    
    st.rerun()

###################################################################################################
### 문서 임베딩화 후 저장

def save_file_embedding(documents_folder_path):
    
    ## 저장할 시간으로 폴더 및 파일 명 생성
    global now_date
    global now_time
    
    uploaded_files = st.file_uploader("Upload your file",type=['pdf','docx'],accept_multiple_files=True)
    file_embedding_process = st.button("Uploaded files done.")

    if file_embedding_process:
        
        for uploaded_file in uploaded_files:
            
            #######################################################################################
            
            file_name = '.'.join(uploaded_file.name.split('.')[:-1])
            
            #######################################################################################
            
            ### 기존 같은 이름의 문서가 있으면 삭제
            if file_name in list(st.session_state.mapping_dict.values()):
                for folder_name, value in st.session_state.mapping_dict.items():
                    if value == file_name:
                        del_folder_name = folder_name
                        
                shutil.rmtree(os.path.join(documents_folder_path, del_folder_name))
                del st.session_state.mapping_dict[del_folder_name]
            
            ### 새로운 mapping할 이름 생성
            new_file_name = '_'.join(['f', now_date, now_time.replace(':', ''), f"{random.randint(10, 999)}{random.randint(10, 999)}"])

            while new_file_name in list(st.session_state.mapping_dict.values()):
                new_file_name = '_'.join(['f', now_date, now_time.replace(':', ''), f"{random.randint(10, 999)}{random.randint(10, 999)}"])
            
            #######################################################################################
            ### mapping 결과값 yaml으로 저장
            
            st.session_state.mapping_dict[new_file_name] = file_name
            
            with open(os.path.join(documents_folder_path, 'mapping.yaml'), 'w', encoding='utf-8') as file:
                yaml.dump(st.session_state.mapping_dict, file, allow_unicode=True)
            
            #######################################################################################
            
            file_folder_path = os.path.join(documents_folder_path, new_file_name)

            #######################################################################################
            ### 문서에 해당하는 vector값 생성
            
            file_list = get_text_from_documents([uploaded_file])
            file_chunk = get_text_chunks_from_documents(file_list)
            file_vectordb = get_vectorstore_from_documents(file_chunk)
            
            #######################################################################################
            ### 임베딩된 vector값 저장

            if os.path.exists(file_folder_path):
                shutil.rmtree(file_folder_path)
                
            os.mkdir(file_folder_path)
            
            file_vectordb.save_local(file_folder_path, new_file_name)
            
            #######################################################################################

        ### 사전에 정의된 llm 값 삭제 (새로운 문서가 들어왔으니 llm도 다시 생성해야함)
        st.session_state.conversation = None
        st.rerun()

###################################################################################################
### 기존에 저장된 문서 리스트 출력 및 삭제 함수

def file_list_expander(file_folder_path, file_list):
    
    with st.expander("Uploaded Files"):
        
        for document_name in file_list:
            
            if document_name == 'mapping.yaml':
                continue
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write(st.session_state.mapping_dict[document_name])
                
            with col2:
                if st.button("삭제", key = document_name):
                    delete_folder_path = os.path.join(file_folder_path, document_name)
                    
                    ### 삭제 버튼 입력 후, 폴더 존재 여부 확인 후 삭제
                    if os.path.exists(delete_folder_path):
                        shutil.rmtree(delete_folder_path)
                        del st.session_state.mapping_dict[document_name]
                        
                        with open(os.path.join(file_folder_path, 'mapping.yaml'), 'w', encoding='utf-8') as file:
                            yaml.dump(st.session_state.mapping_dict, file, allow_unicode=True)
                        
                        ### 사전에 정의된 llm 값 삭제 (문서가 삭제되었으니 llm도 다시 생성해야함)
                        st.session_state.conversation = None
                        st.rerun()

###################################################################################################
###################################################################################################
### 질문이 입력되면 해당 질문을 llm에 넣어 답변 생성

### 날씨와 같이 생성이 오래 걸리는 task는 stream하게 출력하는 것이 좋기 때문에 stream 변수를 선언함
### 기존 LLMChain이나 ConversationalRetrievalChain 에서는 streamlit에 stream 하게 출력이 안됨
### 임시로 ChatOpenAI 만을 사용해서 stream한 기능을 구현

def answer_question(question, stream = None):
    
    source_documents = None
    
    with st.chat_message("assistant"):
        chain = st.session_state.conversation
        
        with st.spinner("Thinking..."):
            
            #######################################################################################
            
            if not st.session_state.error_code:
                
                try:
                    ### stream 한 출력
                    if stream:
                        placeholder = st.empty()
                        
                        ### prompt와 유저 질문을 llm에 저장
                        chunks = chain.stream(st.session_state.prompt.format(question = question, messages = st.session_state.messages))

                        result = ""
                        
                        ### llm 실행과 동시에 stream한 결과를 반환
                        for chunk in chunks:
                            result = result + chunk.content
                            placeholder.markdown(result)

                        ###########################################################################

                        response = result
                        ### 미구현 (LLMChain은 memory에 해당 변수 관련 기능을 하는데, ChatOpenAI은 아직 구현 안됨)
                        st.session_state.chat_history = 1
                    
                    ### 일반적인 경우 (출력이 짧은 경우, 이 방식을 사용하는 것을 권장함)
                    else:
                        result = chain.invoke({"question": question})

                        ###########################################################################
                        ### 결과를 각종 변수에 저장
                        
                        with get_openai_callback() as cb:
                            if 'chat_history' in result:
                                st.session_state.chat_history = result['chat_history']
                        if 'answer' in result:
                            response = result['answer']
                        elif 'text' in result:
                            response = result['text']
                        if 'source_documents' in result:
                            source_documents = result['source_documents']
                        
                    ###############################################################################
                
                ### 오류 발생시 오류 코드를 반환
                except:
                    st.session_state.error_code = 'e0004'
                    
            #######################################################################################
            
            ### 오류 발생 시, 오류 메세지를 결과에 반영
            if st.session_state.error_code:
                response = error_message()
            
            ### 결과 출력
            if not stream:
                st.markdown(response)
            
    ###############################################################################################
    ### source_documents은 그래프 및 참조 문헌 출력 시 필요
    
    return response, source_documents
    
###################################################################################################
###################################################################################################
### 유사도 검색 시 참조한 자료 출력 및 그래프 데이터 생성

def view_reference(source_documents):
    
    graph_data = {}
    
    with st.expander("참고 문서 확인"):
        if len(source_documents) == 0:
            st.markdown(source_documents[0].metadata['source'], help = source_documents[0].page_content)
            st.session_state['graph_data'] = graph_data.update({
                    0 : {
                        'page_content' : source_documents[0].page_content,
                        'metadata' : source_documents[0].metadata
                    }
                })
            st.session_state['graph_data'] = graph_data
        elif len(source_documents) != 0:
            for i in range(len(source_documents)):
                graph_data.update({
                    i : {
                        'page_content' : source_documents[i].page_content,
                        'metadata' : source_documents[i].metadata
                    }
                })
                if i == 3:
                    break
                
                st.markdown(source_documents[i].metadata['source'], help = source_documents[i].page_content)
            st.session_state['graph_data'] = graph_data

###################################################################################################
### 그래프 데이터를 출력해주는 html 파일 생성

def graph_visualize(query: str, sim_data: Dict):
    chatgpt = ChatOpenAI(temperature = 0)
    
    template = """
        아래 문장에서 가장 핵심이 되는 키워드 1개만 뽑아줘!
        <문장>
        {sentence}
    """
    
    prompt_template = PromptTemplate(input_variables = ['sentence'],
                                    template = template)
    
    net = Network()
    net.add_node('0', label = query, title = 'Main Query', color = 'red')
    
    for k, v in sim_data.items():

        keyword = chatgpt.invoke(prompt_template.format(sentence = v['page_content'])).content
    
        net.add_node(str(int(k) + 1), label=str(keyword), title=f"Content : {v['page_content'][:50]}\n Page: {v['metadata']['page']}\n Similarity :  {round(random.random(), 2)}")
        if int(k) + 1 > 0:
            net.add_edge('0', str(int(k) + 1))
            
    save_path = 'graph_test.html'
    #net.show('graph_test.html', local=False, notebook=False)
    net.write_html('graph_test.html')
    
    return save_path

###################################################################################################
### 생성된 그래프 데이터를 출력

def view_graph():
    
    html_path = graph_visualize(st.session_state['current_query'], st.session_state['graph_data'])
    
    p = open(html_path)
    components.html(p.read(), width =800, height = 600)
    
    # components.iframe('file://' + html_path, width=600, height = 600)
    st.session_state['graph_data'] = None
    st.session_state['current_query'] = None

###################################################################################################
###################################################################################################
### yaml으로부터 llm 생성

def llm_from_yaml(request_app_dict, template_key, question):
    
    now_date = current_date.strftime('%Y%m%d')
    now_time = current_date.strftime('%H:%M:%S')
    
    result = st.session_state.result
    
    template_value = request_app_dict['templates'][template_key]

    ###############################################################################################
    ### from_template이 있는 경우 해당 prompt로 llm 정의
    
    if 'from_template' in template_value:
        
        prompt_template = template_value['from_template'][0]
        
        ###########################################################################################
        ### template에 있는 변수들을 prompt에 대입
        
        input_variables = template_value['input_variables'][0]
        scope_variables = locals()
        kwargs = {key: scope_variables.get(key) for key in input_variables if key in scope_variables}
        prompt_template = prompt_template.format(**kwargs)

        ###########################################################################################
        ### prompt 생성
        prompt = PromptTemplate.from_template(
            template = prompt_template
        )
        
        ### llm 생성
        
        if 'LLMChain' == template_value['llm_model'][0]:
            chain = get_simple_QA(prompt, st.session_state.openai_api_key)
        if 'LLMChain_memory' == template_value['llm_model'][0]:
            chain = get_simple_ConversationChain(prompt, st.session_state.openai_api_key)
        if 'LLM_stream' == template_value['llm_model'][0]:
            chain = get_simple_stream_ConversationChain(st.session_state.openai_api_key)
            st.session_state.prompt = prompt

        ###########################################################################################
        
        ### 마지막에 해당하면 유저의 질문을 받아야 하기 때문에 llm 만 반환
        if 'last' in template_value:
            st.session_state.conversation  = chain
        
        ### llm의 결과를 결과 변수에 저장하여 다음 함수에 전달
        else:
            chain_input_variables = template_value['chain_input_variables'][0]
            chain_scope_variables = locals()
            kwargs = {key: chain_scope_variables.get(key) for key in chain_input_variables if key in chain_scope_variables}

            result = chain.invoke(kwargs)
            st.session_state.result = result['text']
            chain = None
    
    ###############################################################################################
    
    ### source가 필요한 경우 source 데이터 호출
    if 'source' in template_value:
        
        source_file_path = os.path.join('./sources', template_value['source'][0])
        result = result_from_file(template_value['function'], source_file_path)
        st.session_state.result = result
    
    ### template에 작성된 함수를 실행
    elif 'function' in template_value:
    
        if st.session_state.result == None:
            result = result_from_file(template_value['function'])
        else:
            result = result_from_file(template_value['function'], st.session_state.result)
        st.session_state.result = result

###################################################################################################
###################################################################################################