import base64

def encode_image(uploaded_file):
    if uploaded_file is not None:
        # To read file as bytes:
        file_bytes = uploaded_file.getvalue()
        return base64.b64encode(file_bytes).decode('utf-8')