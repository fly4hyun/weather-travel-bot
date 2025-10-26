###################################################################################################
###################################################################################################

import importlib
import yaml

import streamlit as st

###################################################################################################
###################################################################################################
### yaml 파일로부터 dict 생성

def get_dict_from_yaml(yaml_path):
    
    with open(yaml_path, 'r', encoding='utf-8') as file:
        yaml_dict = yaml.safe_load(file)

    return yaml_dict

###################################################################################################
### 함수 이름으로부터 함수 호출 및 실행

def result_from_file(functions, data = None):
    
    for function_python in functions:
        
        utils_llm = importlib.import_module(function_python)
        
        for function_name in functions[function_python]:
            func = getattr(utils_llm, function_name)
            data = func(data)

    return data

###################################################################################################
### error message 반환

def error_message():
    
    with open("./yamls/error.yaml", 'r', encoding='utf-8') as file:
        yaml_dict = yaml.safe_load(file)

    error_msg = '\n\n'.join(yaml_dict[st.session_state.error_code])

    return error_msg

###################################################################################################
###################################################################################################