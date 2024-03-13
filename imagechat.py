import os
import streamlit as st
import shutil
from lyzr import ChatBot

vector_store_params = {
  "vector_store_type": "WeaviateVectorStore",
  "index_name": "IndexName" # first letter should be capital
}

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

data_directory = "data"
os.makedirs(data_directory, exist_ok=True)
remove_existing_files(data_directory)

uploaded_file = st.file_uploader("Choose PDF file", type=["pdf"])

if uploaded_file is not None:
    # Save the uploaded PDF file to the data directory
    file_path = os.path.join(data_directory, uploaded_file.name)
    print(file_path)
    with open(file_path, "wb") as file:
        file.write(uploaded_file.getvalue())

    # Display the path of the stored file
    st.success(f"File successfully saved")


def get_files_in_directory(directory="data"):
    # This function help us to get the file path along with filename.
    files_list = []

    if os.path.exists(directory) and os.path.isdir(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                files_list.append(file_path)

path = get_files_in_directory()
print(path)