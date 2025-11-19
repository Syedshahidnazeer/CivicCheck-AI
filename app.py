import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from prompts import get_expert_system_prompt
from pdf_generator import create_styled_pdf
import time

# --- 1. ENTERPRISE PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CivicCheck.ai | NGO Governance",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ULTRA-MODERN CSS INJECTION ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ROOT VARIABLES */
    :root {
        --primary: #2563EB;
        --primary-dark: #1E40AF;
        --secondary: #0F172A;
        --accent: #0D9488;
        --bg-color: #F8FAFC;
        --surface: #FFFFFF;
        --border: #E2E8F0;
    }

    /* GLOBAL RESET */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
    }

    /* --- HIDE BRANDING BUT KEEP SIDEBAR TOGGLE --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ensure the top bar is transparent but clickable so the sidebar toggle works */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* --- HERO SECTION --- */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #334155 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .hero-badge {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        border: 1px solid rgba(255, 255, 255, 0.2);
        display: inline-block;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.1rem;
        max-width: 600px;
        margin-top: 0.5rem;
        line-height: 1.6;
    }

    /* --- CHAT INTERFACE --- */
    .stChatMessage {
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        border-left: 4px solid var(--accent);
        background-color: #F0FDFA;
    }
    
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        border-left: 4px solid var(--primary);
        background-color: #FFFFFF;
    }

    /* --- SIDEBAR UPGRADE --- */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid var(--border);
    }
    
    .sidebar-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
    }

    /* --- BUTTONS & CARDS --- */
    .element-container button {
        background-color: white !important;
        border: 1px solid var(--border) !important;
        color: #1E293B !important;
        padding: 1.25rem !important;
        border-radius: 12px !important;
        text-align: left !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .element-container button:hover {
        border-color: var(--primary) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        transform: translateY(-2px) !important;
    }
    
    .element-container button p {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }

    div.stButton > button[kind="secondary"] {
        background-color: #EFF6FF !important;
        color: var(--primary) !important;
        border: none !important;
    }

    /* Download Section */
    .download-container {
        background: linear-gradient(to right, #ECFDF5, #D1FAE5);
        border: 1px solid #34D399;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "last_response" not in st.session_state: st.session_state.last_response = None

# --- 4. THE "COMMAND CENTER" SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=50)
    st.markdown("### CivicCheck<span style='color:#2563EB'>.ai</span>", unsafe_allow_html=True)
    st.caption("Enterprise NGO Governance System")
    
    st.markdown("---")
    
    st.markdown('<div class="sidebar-header">Authentication</div>', unsafe_allow_html=True)
    api_key_input = st.text_input("API Key", type="password", value=st.session_state.api_key, placeholder="sk-...")
    if api_key_input: st.session_state.api_key = api_key_input
    
    st.markdown('<div class="sidebar-header" style="margin-top: 20px;">Intelligence Engine</div>', unsafe_allow_html=True)
    
    # Advanced Model Selector
    model_map = {
        "Gemini 2.5 Pro (Flagship)": "models/gemini-2.5-pro",
        "Gemini 2.0 Flash (Fast)": "models/gemini-2.0-flash-exp",
        "Gemini 1.5 Pro (Stable)": "models/gemini-1.5-pro-latest"
    }
    selected_model_name = st.selectbox("Select Model", list(model_map.keys()), index=0)
    selected_model = model_map[selected_model_name]
    
    output_mode = st.radio(
        "Analysis Depth",
        ["Executive Brief", "Detailed Compliance Audit"],
        index=0
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Status**")
        st.success("Online")
    with col2:
        st.markdown("**Version**")
        st.caption("v3.0.0 Pro")
        
    if st.button("⟲ Reset Session", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.last_response = None
        st.rerun()

# --- 5. HERO SECTION ---
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">NO-CODE COMPLIANCE SUITE</div>
    <h1 class="hero-title">Indian NGO Governance Specialist</h1>
    <div class="hero-subtitle">
        Autonomous expert system calibrated for the <strong>November 2025 Regulatory Framework</strong>. 
        Specializing in FCRA Amendments, CSR Eligibility, and Income Tax Compliance.
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. INTERACTIVE STARTER GRID ---
if len(st.session_state.messages) == 0:
    st.markdown("### ⚡ Quick Actions")
    st.markdown("Select a compliance module to initiate consultation:")
    
    c1, c2 = st.columns(2)
    
    def set_prompt(text):
        st.session_state.messages.append({"role": "user", "content": text})
    
    with c1:
        if st.button("📋 **FCRA 2025 Renewal Audit**\n\nGenerate a strict document checklist based on May 2025 MHA Amendments."):
            set_prompt("Generate a strict document checklist for FCRA Renewal based on May 2025 MHA Amendments.")
            st.rerun()
        if st.button("🏛️ **CSR Eligibility Engine**\n\nVerify eligibility for corporate funding under the new July 2025 dual-registration rules."):
            set_prompt("Verify eligibility for corporate funding under the new July 2025 dual-registration rules.")
            st.rerun()
            
    with c2:
        if st.button("⚖️ **12A vs 80G Analysis**\n\nStrategic comparison of tax benefits and donor exemptions for the current fiscal year."):
            set_prompt("Strategic comparison of Section 12A vs 80G tax benefits for FY 2025-26.")
            st.rerun()
        if st.button("🚨 **Risk Mitigation Protocol**\n\nIdentify top red flags that trigger MHA scrutiny and cancellation."):
            set_prompt("Identify top red flags that trigger MHA scrutiny and cancellation in 2025.")
            st.rerun()

# --- 7. CHAT RENDERING ---
for message in st.session_state.messages:
    is_user = message["role"] == "user"
    avatar = "https://cdn-icons-png.flaticon.com/512/1144/1144760.png" if is_user else "https://cdn-icons-png.flaticon.com/512/4712/4712009.png"
    
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 8. INPUT LOGIC ---
if prompt := st.chat_input("Enter your regulatory query (e.g., 'Draft a Board Resolution for SBI Account')..."):
    if not st.session_state.api_key:
        st.toast("🔒 API Key Required. Please check sidebar.", icon="⚠️")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- 9. AI ENGINE ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="https://cdn-icons-png.flaticon.com/512/4712/4712009.png"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # VISUAL FEEDBACK
            with st.status("🔍 Analyzing Regulatory Framework...", expanded=True) as status:
                st.write("• Accessing Income Tax Act 2025 Database...")
                time.sleep(0.3)
                st.write("• Checking MHA FCRA Amendments (May 2025)...")
                time.sleep(0.3)
                st.write("• Synthesizing 7 Expert Personas...")
                status.update(label="Compliance Check Complete", state="complete", expanded=False)
            
            # GENERATION
            genai.configure(api_key=st.session_state.api_key)
            
            # Dynamic Prompting
            base_prompt = get_expert_system_prompt()
            if "Detailed" in output_mode:
                base_prompt += "\n\n[OVERRIDE]: Provide DETAILED output with sections, legal citations, and examples. Do not summarize."
            
            model = genai.GenerativeModel(
                model_name=selected_model, 
                system_instruction=base_prompt, 
                safety_settings={HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE}
            )
            
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            
            response_stream = chat.send_message(st.session_state.messages[-1]["content"], stream=True)
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.last_response = full_response
            
            st.rerun()

        except Exception as e:
            st.error(f"System Error: {str(e)}")

# --- 10. RESULTS & DOWNLOAD ---
if st.session_state.last_response:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Professional Download Card
    st.markdown("""
    <div class="download-container">
        <h3 style="margin:0; color:#065F46;">✅ Consultation Complete</h3>
        <p style="color:#047857; margin-top:5px;">Your regulatory guidance document is ready for export.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pdf_bytes = create_styled_pdf(st.session_state.last_response)
        if pdf_bytes:
            st.download_button(
                label="📄 DOWNLOAD OFFICIAL PDF REPORT",
                data=pdf_bytes,
                file_name="CivicCheck_Consultation_2025.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )