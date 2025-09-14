import base64
import streamlit as st
from openai import AzureOpenAI
import time
from PIL import Image
from io import BytesIO

# Set up page configuration
st.set_page_config(
    page_icon="🖼️", 
    page_title="TookTang AI", 
    initial_sidebar_state="collapsed",
    layout="wide",
    menu_items=None 
)

# System message for AI 
system_message = st.secrets["ai_prompts"]["system_message"]

# Initialize the AzureOpenAI client
@st.cache_resource
def get_openai_client():
    return AzureOpenAI(
        api_key=st.secrets["AZURE_OPENAI_API_KEY"],
        azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-02-15-preview"
    )

client = get_openai_client()

# Initialize session state - CLEAN VERSION
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'result_message' not in st.session_state:
    st.session_state.result_message = ""
if 'popup_start_time' not in st.session_state:
    st.session_state.popup_start_time = 0
# Counters for today's impact
if 'items_sorted_today' not in st.session_state:
    st.session_state.items_sorted_today = 0
if 'users_helped_today' not in st.session_state:
    st.session_state.users_helped_today = 0
if 'weight_sorted_today' not in st.session_state:
    st.session_state.weight_sorted_today = 0.0

def update_impact_stats(ai_response):
    """Update today's impact statistics based on actual trash items and weight"""
    
    # Count actual trash items from AI response
    def count_trash_items_and_weight(response):
        
        # Temporary fallback: if no weight found, use default weights
        if "น้ำหนักประมาณ" in response:
            import re
            weight_match = re.search(r'น้ำหนักประมาณ[:\s]*(\d+)\s*g', response)
            if weight_match:
                weight = int(weight_match.group(1))
                return 1, weight
        
        # Count items and estimate weight if no weight provided
        elif "รายการขยะที่" in response:
            import re
            item_matches = re.findall(r'รายการขยะที่\s*\d+', response)
            item_count = len(item_matches)
            estimated_weight = item_count * 20  # 20g per item estimate
            return item_count, estimated_weight
        
        # Single item without weight - estimate
        elif any(word in response.lower() for word in ["ถังขยะสี", "ถังแดง", "ถังเหลือง"]):
            return 1, 20  # Default 20g
        
        return 0, 0
    
    # Count actual trash items and weight
    trash_count, total_weight = count_trash_items_and_weight(ai_response)
    
    # Update counters
    st.session_state.items_sorted_today += trash_count  # Add actual trash pieces
    st.session_state.users_helped_today += 1  # Still count users (sessions)
    
    # Use actual weight for calculation
    weight_in_kg = total_weight / 1000
    st.session_state.weight_sorted_today += (total_weight / 1000)  # Convert to kg

def process_with_ai(image_base64):
    """Process image with Azure OpenAI"""
    try:
        input_prompt = [{
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}",
                "detail": "high"
            }
        }]
        
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": input_prompt}
            ],
            max_tokens=500,
            temperature=0.0
        )
        
        # Update statistics when AI successfully processes an image
        update_impact_stats(chat_completion.choices[0].message.content)
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการประมวลผลภาพ: {str(e)}"

def show_popup_result(message):
    """Display result as a modal popup"""
    
    # Extract which bin is correct from the AI message
    def get_correct_bin(message):
        message_lower = message.lower()
        
        # Count mentions of each bin color
        red_count = message_lower.count("ถังขยะสีแดง") + message_lower.count("ถังแดง")
        yellow_count = message_lower.count("ถังขยะสีเหลือง") + message_lower.count("ถังเหลือง")
        green_count = message_lower.count("ถังขยะสีเขียว") + message_lower.count("ถังเขียว")
        blue_count = message_lower.count("ถังขยะสีน้ำเงิน") + message_lower.count("ถังน้ำเงิน")
        
        # If multiple items, highlight the most mentioned bin
        # If single item, highlight that bin
        max_count = max(red_count, yellow_count, green_count, blue_count)
        
        if max_count == 0:
            return None
        elif red_count == max_count:
            return "red"
        elif yellow_count == max_count:
            return "yellow"
        elif green_count == max_count:
            return "green"
        elif blue_count == max_count:
            return "blue"
        
        return None
    
    correct_bin = get_correct_bin(message)
    
    # Use Streamlit's modal functionality
    @st.dialog("🗂️ คู่มือการแยกขยะ")
    def show_result_modal():
        st.markdown(message)
        st.markdown("---")
        
        # Bin Guide with highlighting
        st.markdown("### 🗑️ คู่มือถังขยะ")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Red bin
        with col1:
            red_style = """
            <div style="text-align: center; padding: 20px; height: 140px; display: flex; flex-direction: column; justify-content: center; background-color: #ffebee; border: 3px solid #f44336; border-radius: 10px; {}">
                <div style="font-size: 32px; margin-bottom: 8px;">🔴</div>
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">แดง</div>
                <div style="font-size: 12px; color: #666;">ขยะติดเชื้อ</div>
            </div>
            """.format("box-shadow: 0 0 15px #f44336; transform: scale(1.05);" if correct_bin == "red" else "")
            st.markdown(red_style, unsafe_allow_html=True)
        
        # Yellow bin
        with col2:
            yellow_style = """
            <div style="text-align: center; padding: 20px; height: 140px; display: flex; flex-direction: column; justify-content: center; background-color: #fffde7; border: 3px solid #ffeb3b; border-radius: 10px; {}">
                <div style="font-size: 32px; margin-bottom: 8px;">🟡</div>
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">เหลือง</div>
                <div style="font-size: 12px; color: #666;">ขยะรีไซเคิล</div>
            </div>
            """.format("box-shadow: 0 0 15px #ffeb3b; transform: scale(1.05);" if correct_bin == "yellow" else "")
            st.markdown(yellow_style, unsafe_allow_html=True)
        
        # Green bin
        with col3:
            green_style = """
            <div style="text-align: center; padding: 20px; height: 140px; display: flex; flex-direction: column; justify-content: center; background-color: #e8f5e8; border: 3px solid #4caf50; border-radius: 10px; {}">
                <div style="font-size: 32px; margin-bottom: 8px;">🟢</div>
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">เขียว</div>
                <div style="font-size: 12px; color: #666;">ขยะย่อยสลายได้</div>
            </div>
            """.format("box-shadow: 0 0 15px #4caf50; transform: scale(1.05);" if correct_bin == "green" else "")
            st.markdown(green_style, unsafe_allow_html=True)
        
        # Blue bin
        with col4:
            blue_style = """
            <div style="text-align: center; padding: 20px; height: 140px; display: flex; flex-direction: column; justify-content: center; background-color: #e3f2fd; border: 3px solid #2196f3; border-radius: 10px; {}">
                <div style="font-size: 32px; margin-bottom: 8px;">🔵</div>
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">น้ำเงิน</div>
                <div style="font-size: 12px; color: #666;">ขยะทั่วไป</div>
            </div>
            """.format("box-shadow: 0 0 15px #2196f3; transform: scale(1.05);" if correct_bin == "blue" else "")
            st.markdown(blue_style, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Footer message
        st.info("🌱 อย่าลืม: การทำความสะอาดขยะช่วยเพิ่มคุณภาพการรีไซเคิล!")
        
        # Close button
        if st.button("✅ เข้าใจแล้ว", type="primary", use_container_width=True):
            st.session_state.show_result = False
            st.session_state.result_message = ""
            st.rerun()
    
    # Show the modal
    show_result_modal()

def show_info_page():
    """Display TookTang information page"""
    # What is TookTang
    st.markdown("## 🤔 TookTang คืออะไร?")
    st.markdown("""
    AI ที่ช่วยบอกคุณว่า “ขยะชิ้นนี้ควรไปถังไหน” แถมยังแนะนำวิธีทำให้ขยะสะอาดพร้อมรีไซเคิล 
    """)
    
    # How it works
    st.markdown("## 🔧 วิธีการใช้งาน")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📸 ถ่ายภาพ
        ถ่ายภาพขยะที่ต้องการทิ้ง
        """)
    
    with col2:
        st.markdown("""
        ### 🤖 AI ให้คำแนะนำ
        ระบบ AI จะระบุประเภทขยะและถังที่เหมาะสม
        """)
    
    with col3:
        st.markdown("""
        ### 🧽 ล้างขยะและแยกตามประเภท
        ล้างขยะและทิ้งตามที่ AI แนะนำที่ถังที่ระบบแนะนำได้เลย
        """)
    
    # Bin types
    st.markdown("## 🗑️ ประเภทถังขยะ")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background-color: #ffebee; border: 3px solid #f44336; border-radius: 10px; height: 120px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🔴</div>
            <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">แดง</div>
            <div style="font-size: 12px; color: #666;">ขยะติดเชื้อ</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background-color: #fffde7; border: 3px solid #ffeb3b; border-radius: 10px; height: 120px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🟡</div>
            <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">เหลือง</div>
            <div style="font-size: 12px; color: #666;">ขยะรีไซเคิล</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background-color: #e8f5e8; border: 3px solid #4caf50; border-radius: 10px; height: 120px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🟢</div>
            <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">เขียว</div>
            <div style="font-size: 12px; color: #666;">ขยะย่อยสลายได้</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background-color: #e3f2fd; border: 3px solid #2196f3; border-radius: 10px; height: 120px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">🔵</div>
            <div style="font-weight: bold; font-size: 16px; margin-bottom: 4px; color: #000;">น้ำเงิน</div>
            <div style="font-size: 12px; color: #666;">ขยะทั่วไป</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Benefits
    st.markdown("## 🌱 ประโยชน์ของการแยกขยะ")
    st.markdown("""
    - ♻️ **ลดขยะ**: ช่วยลดปริมาณขยะที่ต้องกำจัด
    - 🌍 **ช่วยสิ่งแวดล้อม**: ลดมลพิษและการใช้ทรัพยากรใหม่
    - 💰 **ประหยัด**: สร้างมูลค่าจากการรีไซเคิล
    - 📚 **เรียนรู้**: เพิ่มความรู้เรื่องการจัดการขยะ
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
        <div style="color: #666; font-size: 14px; margin-bottom: 10px;">
            พัฒนาโดยทีม TookTang เพื่อสิ่งแวดล้อมที่ดีขึ้น 🌱
        </div>
        <div style="font-size: 12px;">
            <a href="https://www.instagram.com/tooktang.kmutt/" target="_blank" style="color: #2E8B57; text-decoration: none; margin: 0 10px;">ติดตามพวกเราได้ที่</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main_interface():    
    """Main Interface with navigator"""

    tab1, tab2 = st.tabs(["🗑️ แยกขยะ", "ℹ️ เกี่ยวกับ TookTang"])

    with tab1:
        # Simple layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📹 ถ่ายภาพขยะ")
            
            # Simple camera input
            captured_image = st.camera_input("ถ่ายภาพขยะของคุณ", key="main_camera")
            
            # Process button
            if st.button("🔍 วิเคราะห์ขยะ", type="primary", use_container_width=True):
                if captured_image is None:
                    st.warning('📸 กรุณาถ่ายภาพก่อน')
                else:
                    with st.spinner('🤖 กำลังวิเคราะห์ขยะของคุณ...'):
                        try:
                            # Convert image to base64
                            image_bytes = captured_image.getvalue()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            # Get AI response
                            result = process_with_ai(image_base64)
                            st.session_state.result_message = result
                            st.session_state.show_result = True
                            st.session_state.popup_start_time = time.time()
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
        
        with col2:
            st.markdown("### 📈 Impact ของวันนี้")
            st.metric("รายการที่แยกแล้ว", f"🗑️ {st.session_state.items_sorted_today}")
            st.metric("จำนวนคนทิ้งขยะ", f"👥 {st.session_state.users_helped_today}")
        
        # Show popup result if available
        if st.session_state.show_result and st.session_state.result_message:
            show_popup_result(st.session_state.result_message)
            
            # Auto-hide popup after 8 seconds
            if time.time() - st.session_state.popup_start_time > 8:
                st.session_state.show_result = False
                st.session_state.result_message = ""
                st.rerun()

    with tab2:
        show_info_page()

# Run the interface
main_interface()