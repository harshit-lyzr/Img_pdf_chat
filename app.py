import base64
import streamlit as st
import os
import fitz
import openai
from openai import OpenAI
from io import BytesIO
from PIL import Image
import tempfile
from lyzr import ChatBot
import shutil
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("Lyzr Image and Text PDF Chatbot")
def extract_images(path, output_dir):
    pdf_path = os.path.join('data', path)
    print(pdf_path)
    pdf_document = fitz.open(pdf_path)
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)
        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"{os.path.join(output_dir, os.path.splitext(os.path.basename(pdf_path))[0])}_page{page_number + 1}_image{image_index + 1}.{image_ext}"
            with open(image_filename, "wb") as image_file:
                image_file.write(image_bytes)

    pdf_document.close()

def remove_existing_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)

data_directory = "data"
os.makedirs(data_directory, exist_ok=True)
remove_existing_files(data_directory)

data_image_dir = "data/image"
os.makedirs(data_image_dir, exist_ok=True)
remove_existing_files(data_image_dir)
uploaded_file = st.file_uploader("Choose PDF file", type=["pdf","jpeg","png"])
print(uploaded_file)

if uploaded_file is not None:
    # Save the uploaded PDF file to the data directory
    file_path = os.path.join(data_directory, uploaded_file.name)
    with open(file_path, "wb") as file:
        file.write(uploaded_file.getvalue())

    # Display the path of the stored file
    st.success(f"File successfully saved")

    extract_images(uploaded_file.name, data_image_dir)

def get_all_files(data_directory):
    # List to store all file paths
    file_paths = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(data_directory):
        for file in files:
            # Join the root path with the file name to get the absolute path
            file_path = os.path.join(root, file)
            # Append the file path to the list
            file_paths.append(file_path)

    return file_paths

path = get_all_files(data_image_dir)

def encode_image(image_path, max_image=512):
    with Image.open(image_path) as img:
        width, height = img.size
        max_dim = max(width, height)
        if max_dim > max_image:
            scale_factor = max_image / max_dim
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height))

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str

with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
    temp_file_path = temp_file.name

def generate_text(image_file):
    client = OpenAI()

    max_size = 512  # set to maximum dimension to allow (512=1 tile, 2048=max)
    encoded_string = encode_image(image_file, max_size)

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
    text = chat_completion.choices[0].message.content

    file1 = open(temp_file_path, "w")
    file1.writelines(text)

def rag_image_chat(file_path):
    vector_store_params = {
        "vector_store_type": "WeaviateVectorStore",
        "index_name": "Lyzr_c"  # first letter should be capital
    }

    chatbot = ChatBot.txt_chat(
        input_files=[str(file_path)],
        vector_store_params=vector_store_params,
    )

    return chatbot

def rag_pdf_chat(file_path):
    vector_store_params = {
        "vector_store_type": "WeaviateVectorStore",
        "index_name": "Lyzr_c"  # first letter should be capital
    }

    chatbot = ChatBot.pdf_chat(
        input_files=[str(file_path)],
        vector_store_params=vector_store_params
    )

    return chatbot

for image in path:
    generate_text(image)
if uploaded_file is not None:
    rag1=rag_pdf_chat(os.path.join('data', uploaded_file.name))

if uploaded_file is not None:
    question = st.text_input("Ask a question about the resume:")
    if st.button("Get Answer"):
        rag = rag_image_chat(temp_file_path)
        response =rag.chat(question)
        st.markdown(f"""{response.response}""")