import streamlit as st
import json
import zipfile
import os
import openai
from gtts import gTTS
import base64
import pyttsx3

# 데이터 로딩
# 현재 파일의 위치를 기준으로 data 디렉토리 경로 설정
zip_dir = os.path.join(os.path.dirname(__file__), 'data')  # ZIP 파일들이 위치한 디렉토리

# 디렉토리 유효성 검사
if not os.path.exists(zip_dir):
    raise FileNotFoundError(f"지정된 경로를 찾을 수 없습니다: {zip_dir}")

# 압축 파일 목록 확인
zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]

if zip_files:
    print(f"Found {len(zip_files)} zip files in the directory: {zip_files}")
else:
    raise FileNotFoundError("No zip files found. Please check the directory path.")

# 압축 파일에서 모든 데이터 로드
def load_all_data(zip_dir, zip_files):
    all_data = []
    extracted_dir_base = os.path.join(os.path.dirname(__file__), 'extracted_data')

    for zip_file in zip_files:
        zip_path = os.path.join(zip_dir, zip_file)
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP 파일을 찾을 수 없습니다: {zip_path}")
        extracted_dir = os.path.join(extracted_dir_base, zip_file[:-4])  # 각 압축 파일의 이름으로 디렉토리 생성

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_dir)

        # JSON 파일 리스트를 가져옵니다.
        json_files = [f for f in os.listdir(extracted_dir) if f.endswith('.json')]

        # 각 JSON 파일에서 데이터 추출
        for json_file in json_files:
            file_path = os.path.join(extracted_dir, json_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)  # Ensure the data is parsed as JSON
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)

    return all_data

# 상담 데이터를 추출하여 필요한 형식으로 변환하는 함수
def extract_data(json_data):
    extracted_data = []
    for counseling_record in json_data:
        if isinstance(counseling_record, dict):
            profile = counseling_record.get("Profile", {})
            conversations = counseling_record.get("Conversation", {})

            # 상담 정보 추출
            counseling_info = {
                "persona-ids": profile.get("persona-id", ""),
                "personas": profile.get("persona", ""),
                "emotions": profile.get("emotion", ""),
                "content": []
            }

            # 대화 내용 추출
            for conv_idx, conv_data in conversations.items():
                content = conv_data.get("Content", [])
                for contents in content:
                    counseling_info["content"].append({
                        "content": contents.get("HS01", ""),
                        "content": contents.get("SS01", ""),
                        "content": contents.get("HS02", ""),
                        "content": contents.get("SS02", ""),
                        "content": contents.get("HS03", ""),
                        "content": contents.get("SS03", "")
                    })

            extracted_data.append(counseling_info)

    return extracted_data

# EmotionalChatbot 클래스 정의
class EmotionalChatbot:
    def __init__(self, counseling_data):
        self.counseling_data = counseling_data
        self.current_session = [{"role": "system", "content": "You are a helpful counseling assistant."}]
        self.initial_question = "안녕하세요! 저는 감성 챗봇입니다. "

    # OpenAI를 통해 답변을 생성하는 메소드
    def get_openai_response(self, conversation, api_key):
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model=model,
            messages=conversation
        )
        return response['choices'][0]['message']['content']

    # 대화를 시작하는 메소드
    def chat(self, user_input=None, api_key=None):
        if user_input:
            self.current_session.append({"role": "user", "content": user_input})
        conversation = self.current_session
        response = self.get_openai_response(conversation, api_key)
        self.current_session.append({"role": "assistant", "content": response})
        return response

    # 초기 질문 반환
    def get_initial_question(self):
        return self.initial_question

# 압축 파일에서 모든 데이터 로드
all_data = load_all_data(zip_dir, zip_files)
# 데이터를 필요한 형식으로 추출
extracted_data = extract_data(all_data)

# 챗봇 인스턴스 생성
chatbot = EmotionalChatbot(extracted_data)

# Streamlit 앱
st.title('감성 챗봇')
st.markdown("")
st.caption("A streamlit Emotional chatbot powered by OpenAI ParkWB & LeeGH & LeeSW")

with st.expander("감성 챗봇에 관하여", expanded=False):
    st.write(
        """
        - 본 채팅 프로그램은 AI Hub의 감성 대화 말뭉치 데이터를 활용하여 제작되었습니다.
        - GPT 모델의 선택이 가능합니다.( [기본]gpt-3.5-turbo, gpt-4)
        - Chat GPT API key를 입력하지 않으면 작동이 되지 않으니 주의 바랍니다.
        """)
    st.markdown(" --- ")
    st.write(
        """
        - 이 프로그램은 강남대학교 박우빈, 이건해, 이승우 학생이 공동으로 제작하였습니다.
        """)

with st.sidebar:
    # 사이드바에서 OpenAI API 키 입력 받기
    st.session_state["OPENAI_API"] = st.text_input(label="OPENAI API 키", placeholder="Enter your API key", value="", type="password")
    st.markdown("""<style>div[class*="stTextInput"] > label > div[data-testid="stMarkdownContainer"] > p {font-size: 20px; font-weight: bold;}</style>""", unsafe_allow_html=True)
    st.markdown(" --- ")

    # GPT 모델 선택하기 위한 라디오 버튼 생성
    model = st.radio(label="GPT 모델", options=["gpt-3.5-turbo", "gpt-4"])
    st.markdown("""<style>div[class*="stRadio"] > label > div[data-testid="stMarkdownContainer"] > p {font-size: 20px; font-weight: bold;}</style>""", unsafe_allow_html=True)

    st.markdown(" --- ")

    # TTS 음성 선택하기 위한 라디오 버튼 생성
    tts_voice = st.radio(label="TTS 음성 선택", options=["여성", "남성", "없음"])
    st.markdown("""<style>div[class*="stRadio"] > label > div[data-testid="stMarkdownContainer"] > p {font-size: 20px; font-weight: bold;}</style>""", unsafe_allow_html=True)

    st.markdown(" --- ")

    if st.button(label="🔄️ 리셋"):
        # 리셋 코드
        st.session_state["chat"] = []
        st.session_state["messages"] = [{"role": "assistant", "content": "안녕하세요! 저는 감성 챗봇입니다."}]
        st.session_state["check_reset"] = True

# OpenAI API 키가 입력되지 않았을 경우 경고 메시지를 표시하고 실행을 멈춤
if not st.session_state.get("OPENAI_API"):
    st.info("Please add your OpenAI API key!", icon="⚠️")
    st.stop()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    initial_question = chatbot.get_initial_question()
    st.session_state["messages"].append({"role": "assistant", "content": initial_question})

# 현재 대화 내용 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 사용자 답변 입력
if response := st.chat_input("텍스트를 입력하세요"):
    st.session_state["messages"].append({"role": "user", "content": response})
    st.chat_message("user").write(response)
    response = chatbot.chat(user_input=response, api_key=st.session_state["OPENAI_API"])
    st.session_state["messages"].append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

    if tts_voice != "없음":
        # Assistant 응답을 TTS로 변환
        if tts_voice == "남성":
            lang = 'ko'
            tts = gTTS(text=response, lang=lang, slow=False)
            tts.save("response.mp3")

            # TTS 음성 재생
            audio_file = open("response.mp3", "rb")
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
            <audio autoplay style="display:none">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        elif tts_voice == "여성":
            engine = pyttsx3.init()
            engine.setProperty('voice', 'com.apple.speech.synthesis.voice.samantha')  # 선택된 여성 목소리 설정 (Mac OS의 경우)
            engine.save_to_file(response, 'response.mp3')
            engine.runAndWait()

            # TTS 음성 재생
            audio_file = open("response.mp3", "rb")
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
            <audio autoplay style="display:none">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
