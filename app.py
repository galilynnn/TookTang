import base64
import streamlit as st
from openai import AzureOpenAI
from utils import encode_image

client = AzureOpenAI(api_key=st.secrets["AZURE_OPENAI_API_KEY"],
                     azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
                     api_version="2023-09-15-preview")

#######
st.title("GPT-4V Demo 🖼️")
system_message = st.text_area("**System Prompt**", "Your task is to identify what is in the given image. Be succinct.")
input_pic = st.camera_input("**Photo**")
resolution = st.selectbox('**Image Processing Quality**', ('Low', 'High'))

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
                max_tokens=1200,
                temperature=0)

        message_content = chat_completion.choices[0].message.content

        st.info(message_content)