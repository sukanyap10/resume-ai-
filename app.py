

import streamlit as st
import os
import json
import requests
from datetime import datetime
from fpdf import FPDF
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import base64
from io import BytesIO
import re

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Professional Development Suite",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open("style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Add comprehensive CSS styling if style.css is not found
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .modern-form-container {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .resume-preview {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            color: black;
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            min-height: 800px;
            border: 1px solid #e0e0e0;
        }
        .resume-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        .resume-header h1 {
            font-size: 2.5em;
            margin: 0 0 10px 0;
            color: #333;
            font-weight: bold;
        }
        .contact-info {
            color: #666;
            font-size: 1.1em;
            margin-top: 10px;
        }
        .contact-item {
            margin: 0 5px;
        }
        .contact-separator {
            margin: 0 10px;
            color: #667eea;
        }
        .resume-section {
            margin-bottom: 25px;
        }
        .resume-section h2 {
            color: #333;
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #ddd;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .section-content {
            padding-left: 10px;
            color: #444;
            font-size: 1em;
        }
        .section-item {
            margin-bottom: 15px;
            line-height: 1.7;
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            margin-left: 50px;
        }
        .bot-message {
            background: #f8f9fa;
            color: #333;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 20px;
            margin-right: 50px;
            border-left: 4px solid #667eea;
        }
        .stTextArea > div > div > textarea {
            background: rgba(255,255,255,0.9);
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #c62828;
        }
        .success-message {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #2e7d32;
        }
        </style>
        """, unsafe_allow_html=True)

load_css()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = {}

# Groq API function with better error handling
def chat_with_groq(message, system_prompt="You are a helpful career counselor and mental health assistant."):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: Please set your GROQ_API_KEY in the .env file. You can get an API key from https://console.groq.com/"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        if "choices" in response_data and response_data["choices"]:
            return response_data["choices"][0]["message"]["content"]
        else:
            return "Error: Invalid response from API"
            
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "Error: Connection failed. Please check your internet connection."
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return "Error: Invalid API key. Please check your GROQ_API_KEY."
        elif response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        else:
            return f"Error: HTTP {response.status_code} - {str(e)}"
    except json.JSONDecodeError:
        return "Error: Invalid response format from API"
    except Exception as e:
        return f"Error: {str(e)}"

# AI Enhancement function with better error handling
def enhance_resume_content(field_name, content):
    if not content or not content.strip():
        return content
    
    prompts = {
        'education': f"Enhance this education section for a professional resume. Make it concise and impactful: {content}",
        'experience': f"Enhance this work experience section for a professional resume. Use action verbs and quantify achievements where possible: {content}",
        'skills': f"Organize and enhance this skills section for a professional resume. Group similar skills and present them professionally: {content}",
        'projects': f"Enhance this projects section for a professional resume. Focus on impact and technologies used: {content}",
        'achievements': f"Enhance this achievements section for a professional resume. Make them quantifiable and impactful: {content}",
        'certificates': f"Enhance this certificates section for a professional resume. Present them professionally with dates if available: {content}"
    }
    
    if field_name in prompts:
        enhanced = chat_with_groq(prompts[field_name])
        if enhanced.startswith("Error:"):
            st.error(enhanced)
            return content
        return enhanced
    return content

# Enhanced PDF Generation Class with better error handling
class ResumePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        pass
        
    def add_name_header(self, name, email, phone, location):
        try:
            # Name
            self.set_font('Arial', 'B', 28)
            self.set_text_color(0, 0, 0)
            
            # Handle potential encoding issues
            name_clean = name.encode('latin-1', 'ignore').decode('latin-1') if name else ""
            self.cell(0, 15, name_clean, 0, 1, 'C')
            
            # Contact info
            self.set_font('Arial', '', 10)
            self.set_text_color(100, 100, 100)
            
            # Clean contact info
            email_clean = email.encode('latin-1', 'ignore').decode('latin-1') if email else ""
            phone_clean = phone.encode('latin-1', 'ignore').decode('latin-1') if phone else ""
            location_clean = location.encode('latin-1', 'ignore').decode('latin-1') if location else ""
            
            contact_parts = [part for part in [email_clean, phone_clean, location_clean] if part]
            contact_line = " | ".join(contact_parts)
            
            self.cell(0, 6, contact_line, 0, 1, 'C')
            
            # Line separator
            self.ln(5)
            self.set_draw_color(200, 200, 200)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(10)
        except Exception as e:
            print(f"Error in add_name_header: {e}")
        
    def add_section(self, title, content):
        if not content or not content.strip():
            return
            
        try:
            # Section title
            self.set_font('Arial', 'B', 12)
            self.set_text_color(0, 0, 0)
            title_clean = title.encode('latin-1', 'ignore').decode('latin-1')
            self.cell(0, 8, title_clean.upper(), 0, 1, 'L')
            
            # Underline
            self.set_draw_color(100, 100, 100)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(3)
            
            # Content
            self.set_font('Arial', '', 10)
            self.set_text_color(0, 0, 0)
            
            # Split content into lines and process
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # Clean the line for PDF encoding
                    line_clean = line.encode('latin-1', 'ignore').decode('latin-1')
                    
                    # Check if line starts with bullet point
                    if line_clean.startswith('•') or line_clean.startswith('-'):
                        self.cell(5, 5, '•', 0, 0, 'L')
                        self.cell(0, 5, line_clean[1:].strip(), 0, 1, 'L')
                    else:
                        self.cell(0, 5, line_clean, 0, 1, 'L')
            self.ln(5)
        except Exception as e:
            print(f"Error in add_section: {e}")

def generate_pdf(resume_data):
    try:
        pdf = ResumePDF()
        
        # Header
        if resume_data.get('name'):
            pdf.add_name_header(
                resume_data.get('name', ''),
                resume_data.get('email', ''),
                resume_data.get('phone', ''),
                resume_data.get('location', '')
            )
        
        # Add sections in order
        sections = [
            ('Education', 'education'),
            ('Experience', 'experience'),
            ('Skills', 'skills'),
            ('Projects', 'projects'),
            ('Achievements', 'achievements'),
            ('Certificates', 'certificates')
        ]
        
        for section_title, section_key in sections:
            if resume_data.get(section_key):
                pdf.add_section(section_title, resume_data[section_key])
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

# Format text for HTML display
def format_text_for_html(text):
    if not text:
        return "Not provided"
    
    # Convert newlines to proper HTML breaks
    formatted = text.replace('\n', '<br>')
    # Handle bullet points properly
    formatted = re.sub(r'^[•-]\s*', '• ', formatted, flags=re.MULTILINE)
    return formatted

# Main App Header
st.markdown("""
<div class="main-header">
    <h1>🚀 Professional Development Suite</h1>
    <p>Your complete career management solution</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🎯 Navigation")
    selected = option_menu(
        menu_title=None,
        options=["Resume Builder", "Career Guidance", "Performance Review", "Mental Health Chat"],
        icons=["file-earmark-person", "graph-up", "clipboard-check", "chat-heart"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#667eea", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "color": "#333"},
            "nav-link-selected": {"background-color": "rgba(102,126,234,0.1)", "color": "#667eea"},
        }
    )

# Resume Builder Tab
if selected == "Resume Builder":
    st.header("📄 Resume Builder")
    
    # Single column layout with modern form container
    col1 = st.container()
    
    with col1:
        st.markdown('<div class="modern-form-container">', unsafe_allow_html=True)
        
        st.subheader("📝 Resume Information")
        
        # Personal Information
        with st.expander("Personal Information", expanded=True):
            name = st.text_input("Full Name", value=st.session_state.resume_data.get('name', ''))
            email = st.text_input("Email", value=st.session_state.resume_data.get('email', ''))
            phone = st.text_input("Phone", value=st.session_state.resume_data.get('phone', ''))
            location = st.text_input("Location", value=st.session_state.resume_data.get('location', ''))
        
        # Education
        with st.expander("Education", expanded=True):
            education = st.text_area("Education", value=st.session_state.resume_data.get('education', ''), height=200)
            if st.button("🤖 Enhance Education", key="enhance_edu"):
                if education.strip():
                    with st.spinner("Enhancing education section..."):
                        enhanced = enhance_resume_content('education', education)
                        if not enhanced.startswith("Error:"):
                            st.session_state.resume_data['education'] = enhanced
                            st.success("Education section enhanced!")
                            st.rerun()
                else:
                    st.warning("Please enter education details first.")
        
        # Experience
        with st.expander("Experience", expanded=True):
            experience = st.text_area("Experience", value=st.session_state.resume_data.get('experience', ''), height=250)
            if st.button("🤖 Enhance Experience", key="enhance_exp"):
                if experience.strip():
                    with st.spinner("Enhancing experience section..."):
                        enhanced = enhance_resume_content('experience', experience)
                        if not enhanced.startswith("Error:"):
                            st.session_state.resume_data['experience'] = enhanced
                            st.success("Experience section enhanced!")
                            st.rerun()
                else:
                    st.warning("Please enter experience details first.")
        
        # Skills
        with st.expander("Skills", expanded=True):
            skills = st.text_area("Skills", value=st.session_state.resume_data.get('skills', ''), height=180)
            if st.button("🤖 Enhance Skills", key="enhance_skills"):
                if skills.strip():
                    with st.spinner("Enhancing skills section..."):
                        enhanced = enhance_resume_content('skills', skills)
                        if not enhanced.startswith("Error:"):
                            st.session_state.resume_data['skills'] = enhanced
                            st.success("Skills section enhanced!")
                            st.rerun()
                else:
                    st.warning("Please enter skills first.")
        
        # Projects
        with st.expander("Projects", expanded=True):
            projects = st.text_area("Projects", value=st.session_state.resume_data.get('projects', ''), height=220)
            if st.button("🤖 Enhance Projects", key="enhance_proj"):
                if projects.strip():
                    with st.spinner("Enhancing projects section..."):
                        enhanced = enhance_resume_content('projects', projects)
                        if not enhanced.startswith("Error:"):
                            st.session_state.resume_data['projects'] = enhanced
                            st.success("Projects section enhanced!")
                            st.rerun()
                else:
                    st.warning("Please enter projects first.")
        
        # Achievements
        with st.expander("Achievements", expanded=True):
            achievements = st.text_area("Achievements", value=st.session_state.resume_data.get('achievements', ''), height=180)
            if st.button("🤖 Enhance Achievements", key="enhance_ach"):
                if achievements.strip():
                    with st.spinner("Enhancing achievements section..."):
                        enhanced = enhance_resume_content('achievements', achievements)
                        if not enhanced.startswith("Error:"):
                            st.session_state.resume_data['achievements'] = enhanced
                            st.success("Achievements section enhanced!")
                            st.rerun()
                else:
                    st.warning("Please enter achievements first.")
        
        # Certificates
        with st.expander("Certificates", expanded=True):
            certificates = st.text_area("Certificates", value=st.session_state.resume_data.get('certificates', ''), height=180)
            if st.button("🤖 Enhance Certificates", key="enhance_cert"):
                if certificates.strip():
                    with st.spinner("Enhancing certificates section..."):
                        enhanced = enhance_resume_content('certificates', certificates)
                        if not enhanced.startswith("Error:"):
                            st.session_state.resume_data['certificates'] = enhanced
                            st.success("Certificates section enhanced!")
                            st.rerun()
                else:
                    st.warning("Please enter certificates first.")
        
        # Update session state
        st.session_state.resume_data.update({
            'name': name,
            'email': email,
            'phone': phone,
            'location': location,
            'education': education,
            'experience': experience,
            'skills': skills,
            'projects': projects,
            'achievements': achievements,
            'certificates': certificates
        })
        
        # Generate PDF
        st.markdown("---")
        if st.button("📥 Download PDF Resume", type="primary"):
            if name:
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_data = generate_pdf(st.session_state.resume_data)
                        st.download_button(
                            label="Download Resume PDF",
                            data=pdf_data,
                            file_name=f"{name.replace(' ', '_')}_Resume.pdf",
                            mime="application/pdf"
                        )
                        st.success("PDF generated successfully!")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
            else:
                st.error("Please enter your name first.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Career Guidance Tab
elif selected == "Career Guidance":
    st.header("🎯 Career Guidance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛤️ Career Path Analysis")
        current_role = st.text_input("Current Role", placeholder="Software Developer")
        dream_role = st.text_input("Dream Role", placeholder="Technical Lead")
        experience_level = st.selectbox("Experience Level", ["0-1 years", "2-5 years", "5-10 years", "10+ years"])
        
        if st.button("Generate Career Path", key="career_path"):
            if current_role and dream_role:
                prompt = f"Provide a detailed career path from {current_role} to {dream_role} for someone with {experience_level} experience. Include specific steps, timeline, and required skills."
                with st.spinner("Analyzing career path..."):
                    response = chat_with_groq(prompt)
                    if response.startswith("Error:"):
                        st.error(response)
                    else:
                        st.markdown(f"**Career Path Analysis:**\n\n{response}")
            else:
                st.error("Please fill in both roles.")
    
    with col2:
        st.subheader("🎯 Skills Gap Analysis")
        current_skills = st.text_area("Current Skills", placeholder="JavaScript, HTML, CSS, React")
        target_role = st.text_input("Target Role", placeholder="Full Stack Developer")
        
        if st.button("Analyze Skills Gap", key="skills_gap"):
            if current_skills and target_role:
                prompt = f"Analyze the skills gap for transitioning to {target_role} with current skills: {current_skills}. Provide specific recommendations for skills to develop."
                with st.spinner("Analyzing skills gap..."):
                    response = chat_with_groq(prompt)
                    if response.startswith("Error:"):
                        st.error(response)
                    else:
                        st.markdown(f"**Skills Gap Analysis:**\n\n{response}")
            else:
                st.error("Please fill in required fields.")

# Performance Review Tab
elif selected == "Performance Review":
    st.header("📊 Performance Review Assistant")
    
    # Self Assessment
    st.subheader("🎯 Self Assessment")
    col1, col2 = st.columns(2)
    
    with col1:
        overall_rating = st.slider("Overall Performance Rating", 1, 5, 3)
        achievements = st.text_area("Key Achievements", height=100)
        improvements = st.text_area("Areas for Improvement", height=100)
    
    with col2:
        goals = st.text_area("Goals for Next Period", height=100)
        manager_comments = st.text_area("Manager's Comments", height=100)
        recommendations = st.text_area("Development Recommendations", height=100)
    
    # Generate Review Report
    if st.button("📋 Generate Review Report", type="primary"):
        if achievements or improvements or goals:
            prompt = f"""
            Generate a comprehensive performance review report based on this data:
            - Overall Rating: {overall_rating}/5
            - Key Achievements: {achievements}
            - Areas for Improvement: {improvements}
            - Goals: {goals}
            - Manager Comments: {manager_comments}
            - Recommendations: {recommendations}
            
            Provide a professional summary and action plan.
            """
            
            with st.spinner("Generating review report..."):
                response = chat_with_groq(prompt)
                if response.startswith("Error:"):
                    st.error(response)
                else:
                    st.markdown("### 📄 Performance Review Report")
                    st.markdown(response)
        else:
            st.error("Please fill in at least one section.")

# Mental Health Chat Tab
elif selected == "Mental Health Chat":
    st.header("💬 Mental Health & Wellness Chat")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); 
                padding: 20px; border-radius: 15px; margin-bottom: 20px;">
        <h3>🌟 Welcome to Your Wellness Space</h3>
        <p>This is a safe space to discuss work-related stress, career concerns, or general well-being. 
           I'm here to listen and provide supportive guidance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat History Display
    if st.session_state.chat_history:
        st.subheader("💭 Conversation History")
        
        for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {user_msg}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="bot-message">
                <strong>AI Counselor:</strong> {bot_msg}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat Input
    st.subheader("💬 How are you feeling today?")
    user_input = st.text_area("Share what's on your mind...", height=100)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💌 Send Message", type="primary"):
            if user_input:
                system_prompt = """You are a compassionate mental health assistant and career counselor. 
                Provide supportive, empathetic responses focused on mental well-being, stress management, 
                and career guidance. Always prioritize the person's emotional well-being and provide practical advice."""
                
                with st.spinner("Thinking..."):
                    response = chat_with_groq(user_input, system_prompt)
                    if response.startswith("Error:"):
                        st.error(response)
                    else:
                        st.session_state.chat_history.append((user_input, response))
                        st.rerun()
            else:
                st.error("Please enter a message.")
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; padding: 20px; margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.1);">
    <p>© 2024 Professional Development Suite | Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)