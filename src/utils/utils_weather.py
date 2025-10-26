###################################################################################################
###################################################################################################

import os
import csv
import requests
from datetime import datetime, timedelta
import xmltodict

import streamlit as st

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

###################################################################################################
### 날씨 범주 표시

weather_symbol = [
    "POP: 강수확률 [%]", 
    "PTY: 강수형태 [코드값] [0 : 없음, 1 : 비, 2 : 비/눈, 3 : 눈, 4 : 소나기]", 
    "PCP: 1시간 강수량 [범주 (1 mm)]", 
    "REH: 습도 [%]", 
    "SNO: 1시간 신적설 [범주(1 cm)]", 
    "SKY: 하늘상태 [전운량] [0 ~ 5 : 맑음, 6 ~ 8 : 구름많음, 9 ~ 10 : 흐림]", 
    "TMP: 1시간 기온 [℃]", 
    "TMN: 일 최저기온 [℃]", 
    "TMX: 일 최고기온 [℃]", 
    "UUU: 풍속(동서성분) [m/s]", 
    "VVV: 풍속(남북성분) [m/s]", 
    "WAV: 파고 [M]", 
    "VEC: 풍향 [deg]", 
    "WSD: 풍속 [m/s]", 
]

###################################################################################################
###################################################################################################
### 도시 정보랑 해당 도시의 x,y 값이 있는 csv 파일(기상청 제공)로부터 text chunk 생성

def get_text_chunk_from_csv(source_path):
    
    text_chunks = []
    city_to_xy_mapping = {}
    
    with open(source_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            
            city_name = str([row['first'], row['second'], row['third']]).replace(" ", "")
            xy = str([row['x'], row['y']])
            
            text_chunks.append(city_name)
            city_to_xy_mapping[city_name] = xy
    
    return text_chunks, city_to_xy_mapping

###################################################################################################
### llm으로부터 생성된 도시 시간 정보가 형식에 맞게 출력되었는지 확인

def check_answer(response):
    
    start_index = 0
    end_index = 0
    
    try:
        for i in range(len(response)):
            if response[i] == '[':
                start_index = i
                break
        
        for i in range(len(response) - 1 , 0, -1):
            if response[i] == ']':
                end_index = i
                break
    except:
        st.session_state.error_code = 'e0005'
        
    return response[start_index:end_index + 1]

###################################################################################################
### 도시 이름으로부터 x,y 값 가져오기

def get_xy_from_city(source_path):
    
    text_chunks, city_to_xy_mapping = get_text_chunk_from_csv(source_path)

    source_path = source_path.split('/')
    file_name = source_path[-1].split('.')[0]
    folder_path = '/'.join(source_path[:-1])

    embeddings = HuggingFaceEmbeddings(
        #model_name="Huffon/sentence-klue-roberta-base",
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    ### 저장된 vector 정보가 없을 시, 새로 저장
    if not os.path.exists(os.path.join(folder_path, file_name + '.pkl')):
        
        vectordb = FAISS.from_texts(text_chunks, embeddings)
        vectordb.save_local(folder_path, file_name)
        
    vectordb = FAISS.load_local(folder_path = folder_path, 
                                embeddings = embeddings, 
                                index_name = file_name, 
                                allow_dangerous_deserialization = True)

    ### 데이터 정제
    response = st.session_state.result
    response = check_answer(response).replace(" ", "")
    st.session_state.result = response
    response_list = eval(f"[{response}]")
    cities_info = []

    ### 유사도 기반으로 도시 정보 거져오기
    for city_info in response_list[:-1]:

        similar_name = vectordb.similarity_search(str(city_info), k = 1)[0].page_content
        cities_info.append(city_to_xy_mapping[similar_name])

    ###############################################################################################
    ### 시간 정보 오류 시, 디폴트 값으로 변환
    
    time_info = response_list[-1][0].split(":")

    if len(time_info[0]) != 2:
        time_info[0] == '00'
    
    if len(time_info) != 2:
        time_info = [time_info[0], time_info[0]]

    response_list[-1] = [':'.join(time_info)]

    ###############################################################################################
    ### 도시 정보 및 시간 정보 반환
    
    cities_info.append(response_list[-1])

    return [response_list, cities_info]

###################################################################################################
###################################################################################################
### 기상청 api 관련 정보 선언

url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
service_key = '7i9BdFoGGNdILy59nG6hK7i6D2FIfZvfiBXf%2BEsRXYgLQWCjfjo2JKON9qqBrkZcPA6ovPEkSdM90R8D%2BrCPHw%3D%3D'

full_url = f"{url}?serviceKey={service_key}"

###################################################################################################

current_date = datetime.now()

now_date = current_date.strftime('%Y%m%d')
now_time = current_date.strftime('%H:%M:%S')

###################################################################################################
### 기상청으로부터 해당 도시의 정보 호출

def request_weather_travel(response):
    
    cities_list, cities_xy_info = response
    
    global full_url
    global now_date
    global weather_symbol
    
    i = 0

    cities_info = [weather_symbol]
    time_info = cities_xy_info[-1]
    
    for city_info in cities_xy_info[:-1]:
        city_info = eval(f"[{city_info}]")
        
        nx, ny = city_info[0]
    
        params = {
            'pageNo': '1', 
            'numOfRows': '1000', 
            'dataType': 'XML', 
            'base_date': now_date, 
            'base_time': '0500', 
            'nx': nx, 
            'ny': ny
        }
        
        ### 기상청 api 호출
        try:
            res = requests.get(full_url, params=params)
            xml_data = res.text
            dict_data = xmltodict.parse(xml_data)
            
            api_responses = dict_data['response']['body']['items']['item']
        except:
            st.session_state.error_code = 'e0002'
            st.session_state.error_message = '기상청 홈페이지 오류'
            cities_info = '답변 생성 바로 중지.'
            return cities_info
        
        ### 날씨 정보 정제
        try:
            target_weather_info = period_to_value(now_date, time_info, api_responses)
            converted_weather_info = convert_weather_info(cities_list[i], target_weather_info)
        except:
            st.session_state.error_code = 'e0003'
            st.session_state.error_message = '날씨 정보 오류'
            cities_info = '답변 생성 바로 중지.'
            return cities_info
            
        cities_info.append(converted_weather_info)
        
        i = i + 1
        
    return cities_info

###################################################################################################
### 해당 날짜의 기상 정보 반환

def period_to_value(today: str, time: str, api_responses: list):
    
    #time = ast.literal_eval(time)
    
    time_info = time[0].split(":")
    
    today = datetime.strptime(today, '%Y%m%d')
    start_day = today + timedelta(days=int(time_info[0]))
    end_day = today + timedelta(days=int(time_info[1]))
    start_day = start_day.strftime('%Y%m%d')
    end_day = end_day.strftime('%Y%m%d')
    
    target_weather_info = []
    
    ### 최적화 필요 일단 넘어감
    for api_response in api_responses:
        if api_response['fcstDate'] == start_day or api_response['fcstDate'] == end_day:
            target_weather_info.append(api_response)

    return target_weather_info

###################################################################################################
### 기상청 날씨 정보를 llm prompt로 정달하기 위해 정제

def convert_weather_info(city: str, weather_info):
    
    #city_list = ast.literal_eval(city)
    city_list = city
    city_name = ''.join(city_list)

    start_day = weather_info[0]['fcstDate']
    start_time = weather_info[0]['fcstTime']
    
    converted_weather_info = []
    location_time_info = {'location' : city_name, 'day' : start_day, 'time' : start_time}
    forecast_info = {}
    
    for weather_ in weather_info:
        
        if weather_['fcstTime'] != start_time:
            location_time_info['forecast_info'] = list(forecast_info.items())
            converted_weather_info.append(list(location_time_info.items()))
            start_day = weather_['fcstDate']
            start_time = weather_['fcstTime']
            location_time_info = {'location' : city_name, 'day' : start_day, 'time' : start_time}
            forecast_info = {}
        
        forecast_info[weather_['category']] = weather_['fcstValue']
        
    location_time_info['forecast_info'] = list(forecast_info.items())
    converted_weather_info.append(list(location_time_info.items()))
    
    return converted_weather_info

###################################################################################################
###################################################################################################