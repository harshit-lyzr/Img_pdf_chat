import os
from openai import Client
import streamlit as st
import shutil
from PIL import Image
from io import BytesIO
import base64
from lyzr import ChatBot

client = Client()

st.set_page_config(
    page_title="Lyzr QA Bot",
    layout="centered",
    initial_sidebar_state="auto",
    page_icon="lyzr-logo-cut.png",
)

def remove_existing_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            st.error(f"Error while removing existing files: {e}")

# Set the local directory
data_directory = "data"
os.makedirs(data_directory, exist_ok=True)
remove_existing_files(data_directory)
uploaded_file = st.file_uploader("Choose PDF file", type=["jpeg"])

def get_files_in_directory(directory="data"):
    files_list = []
    if os.path.exists(directory) and os.path.isdir(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                files_list.append(file_path)
    return files_list

def encode_image(image_path, max_size):
    img = Image.open(image_path)
    img.thumbnail((max_size, max_size))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def generate_image_to_text(image_file):
    image = f'{image_file}'
    max_size = 512
    encoded_string = encode_image(image, max_size)

    system_prompt = ("You are an expert at analyzing images with computer vision. In case of error, "
                     "make a full report of the cause of: any issues in receiving, understanding, or describing images")
    user = ("Describe the contents and layout of my image.")

    apiresponse = client.chat.completions.with_raw_response.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {
                        "type": "image_url",
                        "image_url": {"url":
                                          f"data:image/jpeg;base64,{encoded_string}"},
                    },
                ],
            },
        ],
        max_tokens=500,
    )
    debug_sent = apiresponse.http_request.content
    chat_completion = apiresponse.parse()
    texts = chat_completion.choices[0].message.content

    with open("myfile.txt", "w") as file1:
        file1.writelines(texts)

def rag_implementation():
    path = get_files_in_directory()

    generate_image_to_text(path)

    rag = ChatBot.txt_chat(
        input_files=["myfile.txt"],
        llm_params={"model": "gpt-3.5-turbo"},
    )

    return rag

question = st.text_input("Ask a question about the resume:")

if st.button("Get Answer"):
    rag = rag_implementation()
    response = rag.chat(question)
    st.markdown(f"""{response.response}""")

with st.expander("ℹ️ - About this App"):
    st.markdown(
        """
    This app uses Lyzr Core to generate notes from transcribed audio. The audio transcription is powered by OpenAI's Whisper model. For any inquiries or issues, please contact Lyzr.
    """
    )
    st.link_button("Lyzr", url="https://www.lyzr.ai/", use_container_width=True)
    st.link_button(
        "Book a Demo", url="https://www.lyzr.ai/book-demo/", use_container_width=True
    )
    st.link_button(
        "Discord", url="https://discord.gg/nm7zSyEFA2", use_container_width=True
    )
    st.link_button(
        "Slack",
        url="https://join.slack.com/t/genaiforenterprise/shared_invite/zt-2a7fr38f7-_QDOY1W1WSlSiYNAEncLGw",
        use_container_width=True,
    )
