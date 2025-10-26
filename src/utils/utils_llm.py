###################################################################################################
###################################################################################################

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain, LLMChain, ConversationChain

from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

###################################################################################################
###################################################################################################
### 심플한 답변을 위한 chatbot

def get_simple_QA(prompt, openai_api_key):
    #llm = ChatOpenAI(openai_api_key=openai_api_key, model_name = 'gpt-3.5-turbo', temperature=0)
    llm = ChatOpenAI(openai_api_key=openai_api_key, model_name = 'gpt-4-0125-preview', temperature=0)
    
    simple_QA = LLMChain(
            llm=llm, 
            prompt = prompt
        )
    
    return simple_QA

###################################################################################################
### 메모리가 있는 심플한 chatbot (stream 불가능)

def get_simple_ConversationChain(prompt, openai_api_key):

    llm = ChatOpenAI(openai_api_key=openai_api_key, model_name = 'gpt-4-0125-preview', temperature=0)#, streaming=True)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)#, output_key='answer')
    
    simple_QA = LLMChain(
            llm=llm, 
            prompt = prompt, 
            verbose = False,
            memory = memory
        )
    
    return simple_QA

###################################################################################################
### stream을 위한 llm (기본 틀만 사용함 계선 필요)

def get_simple_stream_ConversationChain(openai_api_key):

    llm = ChatOpenAI(openai_api_key=openai_api_key, 
                     model_name = 'gpt-4-0125-preview', 
                     temperature=0, 
                     callbacks=[],#[StreamingStdOutCallbackHandler()],
                     verbose = False)

    return llm

###################################################################################################
### 리트리벌이 존재하는 llm chatbot

def get_conversation_chain(vetorestore, openai_api_key):

    llm = ChatOpenAI(openai_api_key=openai_api_key, model_name = 'gpt-3.5-turbo', temperature=0)
    
    conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            chain_type="stuff", 
            retriever = vetorestore.as_retriever(search_type="mmr", verbose = 1),
            # retriever=vetorestore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold":0.3}), 
            memory=ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer'),
            get_chat_history=lambda h: h,
            return_source_documents=True,
            verbose = False,
        )
    
    return conversation_chain

###################################################################################################
###################################################################################################