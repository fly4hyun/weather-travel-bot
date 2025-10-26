###################################################################################################
###################################################################################################

import os
import tiktoken
# from loguru import logger

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

###################################################################################################
###################################################################################################
### 주어진 텍스트를 토큰화 한 다음 해당 토큰의 길이를 반환

def tiktoken_len(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    return len(tokens)

###################################################################################################
### documents로부터 text 추출 (pdf, docx, pptx)

def get_text_from_documents(docs):
    
    doc_list = []
    
    for doc in docs:
        file_name = doc.name  # doc 객체의 이름을 파일 이름으로 사용
        with open(file_name, "wb") as file:  # 파일을 doc.name으로 저장
            file.write(doc.getvalue())
            # logger.info(f"Uploaded {file_name}")
        if '.pdf' in doc.name:
            loader = PyPDFLoader(file_name)
            documents = loader.load_and_split()
        elif '.docx' in doc.name:
            loader = Docx2txtLoader(file_name)
            documents = loader.load_and_split()
        elif '.pptx' in doc.name:
            loader = UnstructuredPowerPointLoader(file_name)
            documents = loader.load_and_split()

        doc_list.extend(documents)
        
    return doc_list

###################################################################################################
### text로부터 chunk 생성

def get_text_chunks_from_documents(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=tiktoken_len
    )
    chunks = text_splitter.split_documents(text)
    
    return chunks

###################################################################################################
### text chunk로부터 vector 생성

def get_vectorstore_from_documents(text_chunks):
    embeddings = HuggingFaceEmbeddings(
                                        model_name="jhgan/ko-sroberta-multitask",
                                        model_kwargs={'device': 'cpu'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        )
    vectordb = FAISS.from_documents(text_chunks, embeddings)
    return vectordb

###################################################################################################
###################################################################################################
### 생성된 vector를 결함

def load_vectordb_from_documents(documents_folder_path):
    
    folder_list = os.listdir(documents_folder_path)

    embeddings = HuggingFaceEmbeddings(
                                        model_name="jhgan/ko-sroberta-multitask",
                                        model_kwargs={'device': 'cpu'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        )
    
    vectordb = None
    
    ###############################################################################################
    ### vector 결합

    for folder_name in folder_list:
        
        if folder_name == 'mapping.yaml':
            continue
        
        folder_path = os.path.join(documents_folder_path, folder_name)
        
        vectordb_temp = FAISS.load_local(folder_path = folder_path, 
                                    embeddings = embeddings, 
                                    index_name = folder_name, 
                                    allow_dangerous_deserialization = True)
        
        if vectordb == None:
            vectordb = vectordb_temp
        else:
            vectordb.merge_from(vectordb_temp)

    return vectordb

###################################################################################################
###################################################################################################