import base64
import streamlit as st
from openai import AzureOpenAI
from utils import encode_image

client = AzureOpenAI(api_key=st.secrets["AZURE_OPENAI_API_KEY"],
                     azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
                     api_version="2023-09-15-preview")

st.set_page_config(page_icon = "🖼️",
                   page_title="GPT-4V Demo"
                   initial_sidebar_state="collapsed")

#######
st.title("GPT-4V Demo 🖼️")
system_message = st.text_area("**Prompt**", "Your task is to identify what is in the image. Be succinct.")
input_pic = st.camera_input("**Photo**")

with st.sidebar:
    st.subheader("Advanced Settings ⚙️")
    resolution = st.selectbox('**Quality of Image to be processed by GPT-4V**', ('Low', 'High'))
    temperature = st.slider('**Temperature**', min_value=0.0, max_value=2.0, step=0.1, value=0.0)
    seed = st.number_input("**Seed**", min_value=0, max_value=999, step=1)
    max_tokens = st.slider('**Max Tokens**', 1, 500, 250)
    json_mode = st.toggle("**JSON Mode**")
    st.write("*You must prompt the model to output 'JSON'*")

    if json_mode == True:
        response_format = "json_object"
    else:
        response_format = "text"        

if st.button("Run"):
    if input_pic is None:
        st.toast('Please take a photo', icon='⚠️')
    else:
        image_base64 = encode_image(input_pic)

        input_prompt = [{"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{image_base64}",
            "detail": resolution}}]

        chat_completion = client.chat.completions.create(
                model="gpt-4v",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": input_prompt}],
                response_format=response_format,
                max_tokens=max_tokens,
                seed=0,
                temperature=temperature)

        message_content = chat_completion.choices[0].message.content

        st.info(message_content)