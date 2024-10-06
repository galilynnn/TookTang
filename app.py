import base64
import streamlit as st
from openai import AzureOpenAI
from utils import encode_image
from io import BytesIO
from PIL import Image

st.set_page_config(page_icon="🖼️", page_title="GPT-4o mini Demo", initial_sidebar_state="collapsed")

# Initialize the AzureOpenAI client outside of the Streamlit app
@st.cache_resource
def get_openai_client():
    return AzureOpenAI(api_key=st.secrets["AZURE_OPENAI_API_KEY"],
                       azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
                       api_version="2023-03-15-preview")

client = get_openai_client()

st.title("TookTang 🖼️")
system_message = """Model Instructor:Welcome to TookTang App Chatbot!
I’m here to help you manage your waste accurately and efficiently.
You can ask me about:	
•	How to properly sort and dispose of different types of waste by showing you which bin matches your waste.
•	Tips on reducing, reusing, and recycling waste at home or work.
•	Learning more about the Circular Economy principles and how to apply them in your daily life.
•	Questions about local waste management regulations.
Feel free to ask, and I’ll guide you through each step of disposing of your waste responsibly!
Context for the TookTang App:
The TookTang app is designed to simplify waste management by helping users properly sort waste through an AI-powered system that matches waste with the correct bin.
This app educates users on sustainable practices and encourages participation through interactive features.
It supports Circular Economy principles like Rethink, Reuse, Reduce, and Recycle, aiming to reduce the environmental impact of improper waste disposal.
This chatbot is part of TookTang’s mission to foster sustainable waste management practices, reduce environmental harm, and empower individuals to contribute to a cleaner, greener planet.
This is an example of what it should be.
Your permanent prompt: You're a smart AI specialized in the 4Rs of the Circular Economy.
You know exactly what to do and where to dispose of waste, offering friendly suggestions along the way,
Your respond should be short and bullet point, so that it will be easier when dev substract the word for integration process.
Keep in mind that the information provided should based from Thailand information.
"""

input_method = st.radio("Choose input method:", ("Upload Photo", "Take Photo"))

# Function to process the image
@st.cache_data
def process_image(file):
    image = Image.open(file)
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
    return img_byte_arr.getvalue()

if input_method == "Upload Photo":
    uploaded_file = st.file_uploader("**Upload a photo**", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        input_pic = process_image(uploaded_file)
        st.image(input_pic, caption="Uploaded Image", use_column_width=True)
    else:
        input_pic = None
else:
    input_pic = st.camera_input("**Take a photo**")

with st.sidebar:
    st.subheader("Advanced Settings ⚙️")
    resolution = st.selectbox('**Image Quality**', ('low', 'high', 'auto'))
    temperature = st.slider('**Temperature**', min_value=0.0, max_value=2.0, step=0.1, value=0.0)
    seed = st.number_input("**Seed**", min_value=0, max_value=999, step=1)
    max_tokens = st.slider('**Max Tokens**', 1, 4000, 2000)

if st.button("Run"):
    if input_pic is None:
        st.toast('Please provide an image', icon='⚠️')
    else:
        image_base64 = base64.b64encode(input_pic).decode('utf-8') if input_method == "Upload Photo" else encode_image(input_pic)

        input_prompt = [{"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{image_base64}",
            "detail": resolution}}]
        
        with st.spinner('Processing...'):
            try:
                chat_completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": input_prompt}],
                    max_tokens=max_tokens,
                    seed=seed,
                    temperature=temperature)

                message_content = chat_completion.choices[0].message.content
                st.info(message_content)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Please check your API configuration and model availability.")