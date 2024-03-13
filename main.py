import streamlit as st
from openai import Client
from PIL import Image
from io import BytesIO
import base64
import os
from lyzr import ChatBot
import tempfile

# Initialize OpenAI API client
client = Client()

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
    chat_completion = apiresponse.parse()
    texts = chat_completion.choices[0].message.content

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(texts)
        temp_file_path = temp_file.name

    return temp_file_path

def lyzr_rag(file_path):
    vector_store_params = {
        "vector_store_type": "WeaviateVectorStore",
        "index_name": "Lyzzr"
    }

    chatbot = ChatBot.txt_chat(
            input_files=[file_path],
        vector_store_params=vector_store_params,
        )

    return chatbot


# Function to encode image to base64
def encode_image(image_path, max_size):
    img = Image.open(image_path)
    img.thumbnail((max_size, max_size))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Streamlit app
def main():
    st.title("Chat With Your Image")

    # Input file selection
    image_file = st.file_uploader("Upload Image:", type=['jpg', 'png'])

    if image_file is not None:
        st.image(image_file, caption='Uploaded Image.', use_column_width=True)
        temp = generate_image_to_text(image_file)
        question = st.text_input("Ask a question related to the text content")
        if st.button("Ask"):
            if question:
                chatbot = lyzr_rag(temp)
                response = chatbot.chat(question)
                st.write("Chatbot's Response:", response.response)
        else:
            st.warning("Please enter a question.")


if __name__ == "__main__":
    main()
