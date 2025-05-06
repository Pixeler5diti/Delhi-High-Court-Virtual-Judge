import streamlit as st
import os
import tempfile
import sys
import streamlit.components.v1 as components

# Check dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Check for OpenAI availability
try:
    from utils.openai_integration import initialize_openai, is_openai_available, enhance_legal_analysis, get_legal_context, generate_summary
    OPENAI_AVAILABLE = initialize_openai()
except ImportError:
    OPENAI_AVAILABLE = False

# Import other dependencies
from utils.pdf_processor import extract_text_from_pdf
from utils2.vector_store import VectorStore
from utils2.judgment_predictor import predict_judgment
from utils2.visualization import plot_case_similarity

# Set page configuration
st.set_page_config(
    page_title="Delhi HC Virtual Judge",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if they don't exist
if 'processed_document' not in st.session_state:
    st.session_state.processed_document = None
if 'similar_cases' not in st.session_state:
    st.session_state.similar_cases = None
if 'judgment_prediction' not in st.session_state:
    st.session_state.judgment_prediction = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'dependency_check' not in st.session_state:
    st.session_state.dependency_check = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Home"
if 'enhanced_analysis' not in st.session_state:
    st.session_state.enhanced_analysis = None

# Apply custom theme with CSS - Enhanced based on requirements
st.markdown("""
<style>
    /* Import premium fonts - Poppins and Inter for professional look */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Animated Background Canvas for particles effect */
    #particles-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        opacity: 0.3;
    }
    
    /* Base styles for dark mode app */
    .stApp {
        background-color: #0e141e;
        background-image: radial-gradient(circle at 10% 20%, #141e30 0%, #0e1420 90%);
        font-family: 'Poppins', 'Inter', sans-serif;
        color: #e6e7eb;
        overflow-x: hidden;
    }
    
    /* Typography enhancements */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: white !important;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    p, div, span, .stMarkdown p {
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        font-size: 16px;
    }
    
    /* Gold accent color - primary highlight */
    .gold-accent {
        color: #FFD700 !important;
    }
    
    /* Premium button styling with enhanced hover effects */
    .stButton button {
        background: linear-gradient(135deg, #FFD700 0%, #e6b800 100%) !important;
        color: #0e141e !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.8rem !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        text-transform: none !important;
        font-size: 16px !important;
        font-family: 'Poppins', sans-serif !important;
        letter-spacing: 0.3px !important;
    }
    
    .stButton button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 7px 20px rgba(255, 215, 0, 0.4) !important;
        filter: brightness(1.05) !important;
    }
    
    .stButton button:active {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(255, 215, 0, 0.4) !important;
    }
    
    /* Secondary button (ghost) styling */
    .stButton [data-testid="baseButton-secondary"] {
        background: transparent !important;
        border: 2px solid #FFD700 !important;
        color: #FFD700 !important;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.15) !important;
    }
    
    .stButton [data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255, 215, 0, 0.1) !important;
        border-color: #FFD700 !important;
        color: #FFD700 !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 7px 15px rgba(255, 215, 0, 0.2) !important;
    }
    
    /* Hide default elements */
    footer {display: none !important;}
    #MainMenu {visibility: hidden;}
    
    /* Premium glassmorphism container styling */
    .content-container {
        background: rgba(22, 28, 43, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 35px;
        margin-bottom: 28px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
        transition: all 0.4s ease;
    }
    
    .content-container:hover {
        box-shadow: 0 15px 60px rgba(0, 0, 0, 0.3), 0 0 30px rgba(255, 215, 0, 0.05);
        border: 1px solid rgba(255, 215, 0, 0.1);
    }
    
    /* Enhanced feature cards with premium hover effects */
    .feature-card {
        background: rgba(22, 28, 43, 0.7);
        border-radius: 16px;
        padding: 32px;
        height: 100%;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 7px 30px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, transparent 0%, rgba(255, 215, 0, 0.03) 100%);
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3), 0 0 15px rgba(255, 215, 0, 0.1);
        border: 1px solid rgba(255, 215, 0, 0.15);
    }
    
    .feature-card:hover::before {
        opacity: 1;
    }
    
    /* Icon animations for feature cards */
    .feature-icon {
        font-size: 42px;
        color: #FFD700;
        margin-bottom: 24px;
        display: inline-block;
        transition: all 0.5s ease;
    }
    
    .feature-card:hover .feature-icon {
        transform: scale(1.1) rotate(5deg);
        filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));
    }
    
    /* Enhanced subtitle text styling */
    .subtitle {
        color: #a0aec0 !important;
        font-size: 1.15rem;
        line-height: 1.7;
        font-weight: 400;
    }
    
    /* Premium metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: 700 !important;
        background: linear-gradient(to right, #FFD700, #FFC107) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        letter-spacing: -0.5px !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 500 !important;
        color: #a0aec0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Enhanced tab buttons styling */
    button[data-testid="baseButton-secondary"] {
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255, 215, 0, 0.1) !important;
        border-color: #FFD700 !important;
        color: #FFD700 !important;
        transform: translateY(-2px) !important;
    }
    
    button[data-testid="baseButton-primary"] {
        background-color: rgba(255, 215, 0, 0.15) !important;
        border-color: #FFD700 !important;
        color: #FFD700 !important;
        font-weight: 600 !important;
    }
    
    /* Animated blinking cursor */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    
    .cursor {
        display: inline-block;
        width: 3px;
        height: 38px;
        background-color: #FFD700;
        margin-left: 5px;
        animation: blink 1s infinite;
        position: relative;
        top: 8px;
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.7);
    }
    
    /* Text reveal animation */
    @keyframes revealText {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    .reveal-text {
        opacity: 0;
        animation: revealText 0.8s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    }
    
    .reveal-delay-1 { animation-delay: 0.1s; }
    .reveal-delay-2 { animation-delay: 0.3s; }
    .reveal-delay-3 { animation-delay: 0.5s; }
    .reveal-delay-4 { animation-delay: 0.7s; }
    
    /* Typing animation for headings */
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    
    .typing-text {
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        animation: typing 2.5s steps(40, end);
    }
    
    /* Enhanced form elements styling */
    .stTextArea textarea, .stTextInput input {
        background-color: rgba(22, 28, 43, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e6e7eb !important;
        padding: 14px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: rgba(255, 215, 0, 0.5) !important;
        box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.15) !important;
        background-color: rgba(22, 28, 43, 0.9) !important;
    }
    
    /* Enhanced file uploader styling */
    [data-testid="stFileUploader"] {
        background-color: rgba(22, 28, 43, 0.7) !important;
        border: 2px dashed rgba(255, 215, 0, 0.3) !important;
        border-radius: 16px !important;
        padding: 25px !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(255, 215, 0, 0.5) !important;
        background-color: rgba(22, 28, 43, 0.8) !important;
    }
    
    /* Enhanced alert boxes */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: rgba(255, 215, 0, 0.8) !important;
        background-image: linear-gradient(45deg, rgba(255, 215, 0, 0.8) 25%, transparent 25%, transparent 50%, rgba(255, 215, 0, 0.8) 50%, rgba(255, 215, 0, 0.8) 75%, transparent 75%, transparent) !important;
        background-size: 1rem 1rem !important;
        animation: progress-bar-stripes 1s linear infinite !important;
    }
    
    @keyframes progress-bar-stripes {
        0% { background-position: 1rem 0; }
        100% { background-position: 0 0; }
    }
    
    /* Rotating glow animation for highlighted elements */
    @keyframes rotatingGlow {
        0% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.3); }
        50% { box-shadow: 0 0 30px rgba(255, 215, 0, 0.5); }
        100% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.3); }
    }
    
    /* Neon gavel floating animation */
    @keyframes floatEffect {
        0% { filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.6)); transform: translateY(0); }
        50% { filter: drop-shadow(0 0 20px rgba(0, 240, 255, 0.8)); transform: translateY(-7px); }
        100% { filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.6)); transform: translateY(0); }
    }
    
    .glow-effect {
        animation: rotatingGlow 3s infinite;
    }
</style>

<!-- Particles animation for background using vanilla JS -->
<canvas id="particles-canvas"></canvas>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        var canvas = document.getElementById('particles-canvas');
        var ctx = canvas.getContext('2d');
        
        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        
        var particles = [];
        var particleCount = 100;
        
        for (var i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 2 + 1,
                color: 'rgba(255, 215, 0, ' + (Math.random() * 0.15 + 0.05) + ')',
                speedX: Math.random() * 0.5 - 0.25,
                speedY: Math.random() * 0.5 - 0.25
            });
        }
        
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            for (var i = 0; i < particleCount; i++) {
                var particle = particles[i];
                
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
                ctx.fillStyle = particle.color;
                ctx.fill();
                
                // Draw connections between nearby particles
                for (var j = i + 1; j < particleCount; j++) {
                    var particle2 = particles[j];
                    var dx = particle.x - particle2.x;
                    var dy = particle.y - particle2.y;
                    var distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 100) {
                        ctx.beginPath();
                        ctx.strokeStyle = 'rgba(255, 215, 0, ' + (0.1 - distance/1000) + ')';
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(particle.x, particle.y);
                        ctx.lineTo(particle2.x, particle2.y);
                        ctx.stroke();
                    }
                }
                
                // Update particle position
                particle.x += particle.speedX;
                particle.y += particle.speedY;
                
                // Bounce off edges
                if (particle.x < 0 || particle.x > canvas.width) {
                    particle.speedX = -particle.speedX;
                }
                if (particle.y < 0 || particle.y > canvas.height) {
                    particle.speedY = -particle.speedY;
                }
            }
            
            requestAnimationFrame(draw);
        }
        
        draw();
    });
</script>
""", unsafe_allow_html=True)

# Top header row with logo and navigation
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <div style="margin-right: 15px;">
        <img src="https://i.imgur.com/YqcwkC4.png" width="42" alt="gavel icon" style="filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.7));" />
    </div>
    <div>
        <div style="font-weight: bold; color: #FFD700; font-size: 1.6rem;">|Virtual Judge|</div>
        <div style="font-size: 0.9rem; color: #a0aec0;">AI Legal Assistant</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation tabs using Streamlit components
col1, col2, col3, col4, col5 = st.columns(5)

# Create tab buttons
if col1.button("Home", key="tab_home", use_container_width=True, 
              type="primary" if st.session_state.active_tab == "Home" else "secondary"):
    st.session_state.active_tab = "Home"
    st.rerun()

if col2.button("About", key="tab_about", use_container_width=True, 
              type="primary" if st.session_state.active_tab == "About" else "secondary"):
    st.session_state.active_tab = "About"
    st.rerun()
    
if col3.button("Upload", key="tab_upload", use_container_width=True, 
              type="primary" if st.session_state.active_tab == "Upload" else "secondary"):
    st.session_state.active_tab = "Upload"
    st.rerun()
    
if col4.button("Analysis", key="tab_analysis", use_container_width=True, 
              type="primary" if st.session_state.active_tab == "Analysis" else "secondary"):
    st.session_state.active_tab = "Analysis"
    st.rerun()
    
if col5.button("Judge", key="tab_judge", use_container_width=True, 
              type="primary" if st.session_state.active_tab == "Judge" else "secondary"):
    st.session_state.active_tab = "Judge"
    st.rerun()

# Divider
st.markdown("<hr style='border: none; height: 1px; background-color: rgba(255, 255, 255, 0.1); margin: 20px 0;'>", unsafe_allow_html=True)

# Show content based on active tab
if st.session_state.active_tab == "Home":
    # Hero Section - Home Tab
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        st.html("""
        <div class="content-container glass-effect glow-effect" style="padding: 45px;">
            <div style="margin-bottom: 28px;">
                <h1 style="font-size: 3.8rem; font-weight: 700; line-height: 1.2; letter-spacing: -1px;">
                    <span class="typing-text reveal-text reveal-delay-1" style="color: white;">AI-Powered</span><br>
                    <span class="reveal-text reveal-delay-2" style="color: #FFD700;">|Virtual Judge|</span>
                    <span class="cursor"></span>
                </h1>
            </div>
            
            <p class="subtitle reveal-text reveal-delay-3" style="margin-bottom: 35px; font-size: 1.15rem; line-height: 1.6; color: #a0aec0;">
                Experience the future of legal analysis with our AI-driven legal assistance platform. Upload your case documents and receive instant insights and predictions.
            </p>
        </div>
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upload Case Files", use_container_width=True):
                st.session_state.active_tab = "Upload"
                st.rerun()
                
        with col2:
            if st.button("Consult Virtual Judge", use_container_width=True, type="secondary"):
                st.session_state.active_tab = "Judge"
                st.rerun()
    
    with right_col:
        # Enhanced logo with animation effects
        st.markdown("""
        <div class="content-container glass-effect" style="text-align: center; padding: 35px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <div class="reveal-text reveal-delay-1" style="font-size: 75px; margin-bottom: 20px; animation: floatEffect 3s infinite;">
                <img src="https://i.imgur.com/YqcwkC4.png" width="160" alt="gavel icon" style="filter: drop-shadow(0 0 15px rgba(0, 240, 255, 0.7)); transition: all 0.5s ease;" />
            </div>
            <h3 class="reveal-text reveal-delay-2" style="color: #FFD700; margin-bottom: 10px; font-weight: 600; font-size: 1.8rem;">Virtual Judge</h3>
            <p class="reveal-text reveal-delay-3" style="color: #a0aec0; font-weight: 300;">AI-Powered Legal Analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced feature cards with premium animations and styling
    st.markdown("<div class='reveal-text reveal-delay-4'><br></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card reveal-text reveal-delay-4" style="text-align: center; height: 230px;">
            <div class="feature-icon">
                <div style="background: rgba(255, 215, 0, 0.1); border-radius: 50%; width: 90px; height: 90px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; box-shadow: 0 10px 25px rgba(255, 215, 0, 0.2);">   
                    <img src="https://img.icons8.com/fluency/96/scales.png" width="60" alt="scales icon" style="transform: translateY(-2px);" />
                </div>
            </div>
            <h3 style="color: white; margin-bottom: 14px; font-size: 1.45rem; font-weight: 600;">Legal Analysis</h3>
            <p style="color: #a0aec0; font-size: 0.95rem; line-height: 1.5;">AI-powered analysis of legal documents and case files with intelligent reasoning</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card reveal-text reveal-delay-5" style="text-align: center; height: 230px;">
            <div class="feature-icon">
                <div style="background: rgba(255, 215, 0, 0.1); border-radius: 50%; width: 90px; height: 90px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; box-shadow: 0 10px 25px rgba(255, 215, 0, 0.2);">   
                    <img src="https://img.icons8.com/fluency/96/search.png" width="60" alt="search icon" style="transform: translateY(-2px);" />
                </div>
            </div>
            <h3 style="color: white; margin-bottom: 14px; font-size: 1.45rem; font-weight: 600;">Case Similarity</h3>
            <p style="color: #a0aec0; font-size: 0.95rem; line-height: 1.5;">Find similar cases in our comprehensive database for precedent research</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card reveal-text reveal-delay-6" style="text-align: center; height: 230px;">
            <div class="feature-icon">
                <div style="background: rgba(255, 215, 0, 0.1); border-radius: 50%; width: 90px; height: 90px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; box-shadow: 0 10px 25px rgba(255, 215, 0, 0.2);">   
                    <img src="https://img.icons8.com/fluency/96/bot.png" width="60" alt="robot icon" style="transform: translateY(-2px);" />
                </div>
            </div>
            <h3 style="color: white; margin-bottom: 14px; font-size: 1.45rem; font-weight: 600;">AI Predictions</h3>
            <p style="color: #a0aec0; font-size: 0.95rem; line-height: 1.5;">Get judgment predictions based on case facts and established legal precedents</p>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.active_tab == "About":
    st.markdown("""<h1 class='reveal-text reveal-delay-1' style='text-align: center; color: #4B9FE1; font-size: 2.8rem; margin-bottom: 40px;'>ABOUT US</h1>""", unsafe_allow_html=True)
    
    # About content with animation effects
    st.html("""
    <div class="content-container glass-effect reveal-text reveal-delay-2">
        <p style="font-size: 1.1rem; line-height: 1.7; margin-bottom: 20px;">
            Virtual Judge is an AI-powered legal assistance platform that leverages a fine-tuned LegalBERT model to streamline judicial processes and support legal analysis.
        </p>
        
        <p style="font-size: 1.1rem; line-height: 1.7; margin-bottom: 20px;">
            This application is designed to analyze uploaded legal documents—such as case descriptions, petitions, or judgments—and extract key legal semantics. It then searches the case database to identify the most relevant precedents based on contextual and legal similarity.
        </p>
        
        <p style="font-size: 1.1rem; line-height: 1.7; margin-bottom: 20px;">
            By comparing the current case with historical judgments, the system predicts possible outcomes, offering data-driven insights to lawyers, litigants, or researchers.
        </p>
        
        <p style="font-size: 1.1rem; line-height: 1.7;">
            The integration of Natural Language Processing (NLP) with legal domain knowledge enables Virtual Judge to provide meaningful case recommendations, enhance legal research efficiency, and simulate judgment reasoning in ways that support legal professionals.
        </p>
    </div>
    """)
    
    # Technical capabilities
    st.markdown("""<h2 class='reveal-text reveal-delay-3' style='margin-top: 30px; margin-bottom: 20px;'>Technical Capabilities</h2>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card reveal-text reveal-delay-4" style="height: 100%;">
            <h3 style="color: #FFD700; margin-bottom: 15px;">LegalBERT Model</h3>
            <p>Our core AI system utilizes a fine-tuned version of LegalBERT, specifically trained on legal documents to understand legal terminology, reasoning, and precedents.</p>
            <ul style="color: #a0aec0; margin-top: 15px;">
                <li style="margin-bottom: 8px;">Fine-tuned on 100,000+ legal documents</li>
                <li style="margin-bottom: 8px;">Context-aware legal reasoning</li>
                <li style="margin-bottom: 8px;">Specialized legal entity recognition</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card reveal-text reveal-delay-5" style="height: 100%;">
            <h3 style="color: #FFD700; margin-bottom: 15px;">Vector Search Technology</h3>
            <p>Our similarity engine transforms legal documents into high-dimensional vectors to find conceptually similar cases in milliseconds.</p>
            <ul style="color: #a0aec0; margin-top: 15px;">
                <li style="margin-bottom: 8px;">Semantic search capabilities</li>
                <li style="margin-bottom: 8px;">Multi-dimensional similarity analysis</li>
                <li style="margin-bottom: 8px;">Contextual relevance ranking</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.active_tab == "Upload":
    st.header("Upload Legal Document")
    
    # Custom CSS & HTML for PDF Upload
    upload_html = """
    <style>
    .upload-card {
        background-color: rgba(22, 28, 43, 0.7);
        border: 2px dashed rgba(255, 215, 0, 0.3);
        padding: 30px;
        border-radius: 16px;
        text-align: center;
        transition: 0.3s;
        margin-bottom: 20px;
    }
    .upload-card:hover {
        border-color: rgba(255, 215, 0, 0.5);
        background-color: rgba(22, 28, 43, 0.8);
    }
    .upload-icon {
        font-size: 100px;
        color: #FFD700;
    }
    .upload-text {
        font-size: 18px;
        color: #e6e7eb;
        margin-top: 10px;
    }
    </style>

    <div class="upload-card">
        <div class="upload-icon">📄</div>
        <div class="upload-text"><strong>Upload your Legal Document (PDF)</strong></div>
        <p style="color: #a0aec0;">Only PDF files are supported. Max size: 20MB</p>
    </div>
    """

    # Display custom upload UI
    st.markdown(upload_html, unsafe_allow_html=True)

    # Streamlit uploader (functional, underneath styled block)
    uploaded_file = st.file_uploader("Choose PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_file is not None:
        st.success("✅ PDF uploaded successfully!")

        with st.spinner("Processing document..."):
            # Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                # Extract text from PDF
                document_text = extract_text_from_pdf(tmp_file_path)
                # Display document preview
                st.subheader("Document Preview")
                preview_text = document_text[:1000] + "..." if len(document_text) > 1000 else document_text
                #print(preview_text)
                
                st.text_area("Document Content (Preview)", preview_text, height=250)

                # Generate document summary with OpenAI if available
                if OPENAI_AVAILABLE:
                    with st.spinner("Generating document summary with GPT-4o..."):
                        try:
                            summary = generate_summary(document_text, max_words=300)
                            st.subheader("AI-Generated Document Summary")
                            st.info(summary)
                        except Exception as e:
                            st.error(f"Error generating document summary: {str(e)}")

                # Save processed document in session state for other tabs
                st.session_state.processed_document = document_text

                # Initialize vector store and find similar cases
                vector_store = VectorStore()
                st.session_state.similar_cases = vector_store.find_similar_cases(document_text, top_k=5)

                # Generate judgment prediction
                st.session_state.judgment_prediction = predict_judgment(document_text, st.session_state.similar_cases)

                # If OpenAI is available, enhance the analysis with GPT-4o
                if OPENAI_AVAILABLE and 'judgment_prediction' in st.session_state:
                    with st.spinner("Enhancing analysis with GPT-4o..."):
                        try:
                            enhanced_analysis = enhance_legal_analysis(
                                document_text=document_text,
                                predicted_outcome=st.session_state.judgment_prediction['prediction'],
                                confidence=st.session_state.judgment_prediction['confidence'],
                                legal_principles=st.session_state.judgment_prediction['legal_principles'],
                                liability_determination=st.session_state.judgment_prediction['liability_determination']
                            )
                            
                            # Save in session state
                            st.session_state.enhanced_analysis = enhanced_analysis
                            
                        except Exception as e:
                            st.error(f"Error enhancing analysis with GPT-4o: {str(e)}")
                            st.session_state.enhanced_analysis = None

                st.success("Document processed successfully! Navigate to the 'Analysis' and 'Judge' tabs to see results.")

            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

elif st.session_state.active_tab == "Analysis":
    st.header("Similar Legal Cases")
    
    if not st.session_state.similar_cases:
        st.info("Please upload a document in the 'Upload' tab to see similar cases.")
    else:
        print(st.session_state.similar_cases)
        # Display similar cases
        for i, case in enumerate(st.session_state.similar_cases):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(case['title'])
                    st.caption(f"Case ID: {case['case_id']} | Judgment Date: {case['judgment_date']}")
                    st.write(case['summary'])
                    st.caption(f"Outcome: {case['outcome']}")
                
                with col2:
                    st.metric("Similarity", f"{case['similarity']:.2f}")
        
        # Display visualization
        st.subheader("Case Similarity Analysis")
        plot_case_similarity(st.session_state.similar_cases)

elif st.session_state.active_tab == "Judge":
    st.header("AI Judgment Prediction")
    
    if not st.session_state.judgment_prediction:
        st.info("Please upload a document in the 'Upload' tab to see judgment predictions.")
    else:
        prediction = st.session_state.judgment_prediction
        print(prediction)
        # Summary, Legal Analysis, Confidence tabs
        pred_tab1, pred_tab2, pred_tab3 = st.tabs(["Summary", "Legal Analysis", "Confidence Assessment"])
        
        with pred_tab1:
            st.markdown(f"<h2 style='text-align: center;'>Predicted Judgment</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: #FFD700;'>{prediction['prediction']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>Confidence: <strong>{prediction['confidence']*100:.1f}%</strong></p>", unsafe_allow_html=True)
            
            # Get judgment summary for the speaking judge
            judgment_summary = f"""
            Prediction: {prediction['prediction']}
            Confidence Score: {prediction['confidence']:.2f}
            
            Key reasoning: {prediction['reasoning'][:200]}...
            """
            
            # Judge animation HTML
            judge_html = """
            <style>
    body {
      font-family: Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
      background-color: #f0f4f8;
      background-image: linear-gradient(to bottom, #e6ebf0, #f0f4f8);
    }
    
    .container {
      display: flex;
      flex-direction: column;
      align-items: center;
      max-width: 800px;
      width: 100%;
    }
    
    .judge-container {
      position: relative;
      width: 300px;
      height: 400px;
      margin-bottom: 20px;
      filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2));
    }
    
    #judge-component {
  position: relative;
}

.speech-bubble {
  position: absolute;
  top: 40px;
  left: 50%;
  transform: translateX(-50%);
  background-color: white;
  border-radius: 20px;
  padding: 15px;
  width: 200px;
  min-height: 80px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  display: none;
  z-index: 10;
  font-family: 'Georgia', serif;
  font-style: italic;
}

    
    .speech-bubble:before {
  content: '';
  position: absolute;
  bottom: -15px;
  left: 50%;
  transform: translateX(-50%);
  border-width: 0 15px 15px 15px;
  border-style: solid;
  border-color: white transparent transparent transparent;
}

    
    .controls {
      display: flex;
      flex-direction: column;
      width: 80%;
      gap: 10px;
      margin-top: 20px;
    }
    
    textarea {
      width: 100%;
      height: 100px;
      padding: 10px;
      border-radius: 5px;
      border: 1px solid #ccc;
      resize: vertical;
      font-family: 'Georgia', serif;
    }
    
    button {
      padding: 12px 20px;
      background-color: #3a3a8c;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-weight: bold;
      transition: all 0.2s ease;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2));
    }
    
    button:hover {
      background-color: #2a2a6c;
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.3));
    }
    
    button:active {
      transform: translateY(0);
    }
    
    .mouth {
      transition: all 0.1s ease;
    }
    
    .judge-robe {
      fill: #000022;
      stroke: #333;
      stroke-width: 1;
    }
    
    .judge-face {
      fill: #f8d5c2;
      stroke: #d4b6a0;
      stroke-width: 0.5;
    }
    
    .judge-hair {
      fill: #f8d5c2;
      stroke: #f8d5c2;
      stroke-width: 0.5;
    }
    
    .judge-gavel {
      fill: #8b4513;
      stroke: #5c2c0d;
      stroke-width: 0.5;
    }
    
    .judge-gavel-handle {
      fill: #5c2c0d;
      stroke: #3d1d08;
      stroke-width: 0.5;
    }
    
    .judge-collar {
      fill: white;
      stroke: #eee;
      stroke-width: 0.5;
    }
    
    .status {
      margin-top: 10px;
      font-style: italic;
      color: #f4eaea;
    }
    
    h1 {
      color: #d9d5d5;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.1));
      margin-bottom: 30px;
    }
  </style>
</head>
            <div class="judge-container">
              <div id="judge-component">
                <svg id="judgeSvg" width="300" height="400" viewBox="0 0 300 400">
                  <!-- Court Background -->
                  <rect x="0" y="0" width="300" height="400" fill="#2a1506" />
                  <rect x="20" y="20" width="260" height="200" fill="#402010" />
                  <rect x="40" y="40" width="220" height="160" fill="#8B4513" />
                  <path d="M50 50 L250 50 L250 190 L50 190 Z" fill="#5c2c0d" />
                  
                  <!-- Indian Flag -->
                  <rect x="230" y="70" width="30" height="10" fill="#ffa652" />
                  <rect x="230" y="80" width="30" height="10" fill="#fff" />
                  <rect x="230" y="90" width="30" height="10" fill="#52a447" />
                  <rect x="230" y="100" width="30" height="10" fill="#fff" />
                  <rect x="230" y="110" width="30" height="10" fill="#ffa652" />
                  
                  <!-- Judge's Bench -->
                  <rect x="50" y="200" width="200" height="180" fill="#4d2c09" />
                  <rect x="60" y="210" width="180" height="160" fill="#754c24" rx="5" ry="5" />
                  <rect x="70" y="220" width="160" height="30" fill="#5c391c" />
                  
                  <!-- Judge's Body / Robe -->
                  <path class="judge-robe" d="M90 170 L90 350 L210 350 L210 170 C170 190 130 190 90 170 Z" fill="#000022" stroke="#333" stroke-width="1" />
                  
                  <!-- Judge's Red Tie -->
                  <path d="M140 180 L130 250 L150 280 L170 250 L160 180 Z" fill="#cc0000" stroke="#aa0000" stroke-width="1" />
                  <path d="M140 180 L160 180 L150 190 Z" fill="#aa0000" />
                  
                  <!-- Judge's Shirt/Collar -->
                  <path d="M110 170 L190 170 L190 190 L110 190 Z" fill="white" stroke="#ddd" stroke-width="0.5" />
                  <path d="M140 180 L140 220 L160 220 L160 180 Z" fill="white" stroke="#ddd" stroke-width="0.5" />

                  <!-- Judge's Face -->
                  <ellipse class="judge-face" cx="150" cy="110" rx="45" ry="50" fill="#f8d5c2" stroke="#d4b6a0" stroke-width="0.5" />

                  <!-- Judge's Ears -->
                  <ellipse class="judge-face" cx="105" cy="110" rx="8" ry="15" fill="#f8d5c2" stroke="#d4b6a0" stroke-width="0.5" />
                  <ellipse class="judge-face" cx="195" cy="110" rx="8" ry="15" fill="#f8d5c2" stroke="#d4b6a0" stroke-width="0.5" />

                  <!-- Judge's Neck -->
                  <path class="judge-face" d="M140 150 L140 180 L160 180 L160 150 Z" fill="#f8d5c2" stroke="#d4b6a0" stroke-width="0.5" />
                  
                  <!-- Judge's Black Judicial Wig -->
                  <!-- Wig Base -->
                  <path class="judge-hair" d="M100 70 Q100 40 150 40 Q200 40 200 70 L200 120 Q200 130 190 130 L110 130 Q100 130 100 120 Z" fill="#f8d5c2" stroke="#d4b6a0" stroke-width="0.5" />
                  
                  <!-- Wig Curls - Top -->
                  <path d="M105 50 Q110 40 115 50 Q120 40 125 50 Q130 40 135 50 Q140 40 145 50 Q150 40 155 50 Q160 40 165 50 Q170 40 175 50 Q180 40 185 50 Q190 40 195 50" fill="#222" stroke="#333" stroke-width="0.5" />
                  
                  <!-- Wig Curls - Sides -->
                  <path d="M100 70 Q95 75 100 80 Q95 85 100 90 Q95 95 100 100 Q95 105 100 110 Q95 115 100 120" fill="#222" stroke="#333" stroke-width="0.5" />
                  <path d="M200 70 Q205 75 200 80 Q205 85 200 90 Q205 95 200 100 Q205 105 200 110 Q205 115 200 120" fill="#222" stroke="#333" stroke-width="0.5" />
                  
                  <!-- Judge's Eyes with tensed expression -->
                  <ellipse cx="135" cy="100" rx="8" ry="5" fill="white" stroke="black" stroke-width="1" />
                  <ellipse cx="165" cy="100" rx="8" ry="5" fill="white" stroke="black" stroke-width="1" />
                  <circle cx="135" cy="100" r="3" />
                  <circle cx="165" cy="100" r="3" />
                  <circle cx="134" cy="99" r="1" fill="white" />
                  <circle cx="164" cy="99" r="1" fill="white" />
                  
                  <!-- Judge's Eyebrows - tensed expression -->
                  <path d="M120 85 Q135 80 150 85" stroke="black" stroke-width="2" fill="none" />
                  <path d="M150 85 Q165 80 180 85" stroke="black" stroke-width="2" fill="none" />
                  
                  <!-- Judge's Nose -->
                  <path d="M150 105 L145 120 L155 120 Z" stroke="#d4b6a0" stroke-width="1" fill="#e6c7b3" />
                  
                  <!-- Stress lines on forehead -->
                  <path d="M130 75 L140 78" stroke="#d4b6a0" stroke-width="0.5" fill="none" />
                  <path d="M160 78 L170 75" stroke="#d4b6a0" stroke-width="0.5" fill="none" />
                  <path d="M145 70 L155 70" stroke="#d4b6a0" stroke-width="0.5" fill="none" />
                  
                  <!-- Judge's Mouth (will be animated) -->
                  <path id="mouth" class="mouth" d="M135 135 Q150 140 165 135" stroke="#a87b6d" stroke-width="1.5" fill="none" />
                  
                  <!-- Judge's Gavel in hand -->
                  <path d="M190 300 Q200 290 210 300 L220 320 Q210 330 200 320 Z" fill="#f8d5c2" stroke="#d4b6a0" stroke-width="0.5" /><!-- Hand -->
                  <rect id="gavel-handle" x="200" y="285" width="8" height="50" rx="2" fill="#5c2c0d" stroke="#3d1d08" stroke-width="0.5" />
                  <path id="gavel-head" d="M190 275 L220 275 L220 285 L190 285 Z" fill="#8b4513" stroke="#5c2c0d" stroke-width="0.5" />
                </svg>
                
                <div id="speechBubble" style="position: absolute; top: 30px; right: -150px; background-color: white; border-radius: 20px; padding: 15px; width: 200px; min-height: 80px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: none; z-index: 10; font-family: 'Georgia', serif; font-style: italic;">
                  <p id="speechText"></p>
                </div>
              </div>
              
              <button id="speakButton" style="padding: 12px 20px; background-color: #3a3a8c; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-top: 15px;">Have Judge Announce Verdict</button>
              <p id="status" style="font-style: italic; color: #444; margin-top: 5px;">Ready to speak</p>
            </div>

            <script>
              // Store the judgment text for the speech
              const judgmentText = `""" + judgment_summary.replace("`", "'").replace("\"", "'") + """`;
              
              // Get the speech bubble and other elements
              const speechBubble = document.getElementById('speechBubble');
              const speechText = document.getElementById('speechText');
              const speakButton = document.getElementById('speakButton');
              const mouth = document.getElementById('mouth');
              const status = document.getElementById('status');
              const gavelHead = document.getElementById('gavel-head');
              const gavelHandle = document.getElementById('gavel-handle');
              
              // Check if browser supports speech synthesis
              const synth = window.speechSynthesis;
              let speaking = false;
              
              // Animation frames for mouth movement with more natural curves
              const mouthClosed = "M135 135 Q150 140 165 135";
              const mouthOpen = "M135 135 Q150 155 165 135";
              const mouthHalfOpen = "M135 135 Q150 145 165 135";
              const mouthTense = "M135 138 Q150 136 165 138";
              
              // Get all voices and select a deep male voice if available
              let voices = [];
              function populateVoiceList() {
                voices = synth.getVoices();
              }
              
              if (synth.onvoiceschanged !== undefined) {
                synth.onvoiceschanged = populateVoiceList;
              }
              populateVoiceList();
              
              // Function to find the best judicial voice (deep male voice)
              function findJudicialVoice() {
                // Default to first voice
                let judicialVoice = voices[0];
                
                // Try to find a deep male English voice
                for (let voice of voices) {
                  if (voice.lang.includes('en') && voice.name.toLowerCase().includes('male')) {
                    judicialVoice = voice;
                    break;
                  }
                }
                
                return judicialVoice;
              }
              
              speakButton.addEventListener('click', () => {
                if (speaking) {
                  synth.cancel();
                  resetJudge();
                  return;
                }
                
                // Show speech bubble with text
                speechText.textContent = judgmentText;
                speechBubble.style.display = 'block';
                
                // Update button text
                speakButton.textContent = "Stop Speaking";
                
                // Animate the judge
                speaking = true;
                status.textContent = "Judge is speaking...";
                
                // Start mouth and eyebrow animations
                animateMouth();
                animateEyebrows();
                
                // Use speech synthesis if available
                if (synth) {
                  const utterance = new SpeechSynthesisUtterance(judgmentText);
                  utterance.rate = 0.85; // Slower for judge-like gravitas
                  utterance.pitch = 0.7; // Deeper voice
                  
                  // Try to use a judicial voice
                  const judicialVoice = findJudicialVoice();
                  if (judicialVoice) {
                    utterance.voice = judicialVoice;
                  }
                  
                  utterance.onend = () => {
                    resetJudge();
                  };
                  
                  // Add gavel animation
                  gavelInterval = setInterval(animateGavel, 1500);
                  
                  // Add word boundary event to sync mouth with speech
                  utterance.onboundary = (event) => {
                    if (event.name === 'word') {
                      // Open mouth more at the beginning of each word
                      mouth.setAttribute('d', mouthOpen);
                      setTimeout(() => {
                        if (speaking) {
                          mouth.setAttribute('d', Math.random() > 0.5 ? mouthHalfOpen : mouthClosed);
                        }
                      }, 100);
                    }
                  };
                  
                  synth.speak(utterance);
                } else {
                  // If speech synthesis is not available, just animate for a few seconds
                  setTimeout(resetJudge, 5000);
                }
              });
              
              // More natural lip-synced mouth animation
              function animateMouth() {
                if (!speaking) return;
                
                // More realistic speaking pattern
                const mouthPositions = [
                  mouthOpen, mouthHalfOpen, mouthClosed, mouthHalfOpen, 
                  mouthOpen, mouthClosed, mouthTense, mouthHalfOpen
                ];
                
                const randomIndex = Math.floor(Math.random() * mouthPositions.length);
                mouth.setAttribute('d', mouthPositions[randomIndex]);
                
                // Vary the animation speed for more natural speech
                const animationSpeed = 80 + Math.random() * 120;
                setTimeout(animateMouth, animationSpeed);
              }
              
              // Add eyebrow animation for tensed expression
              function animateEyebrows() {
                if (!speaking) return;
                
                const eyebrows = document.querySelectorAll('path[stroke="black"][stroke-width="2"]');
                
                // Create tensed expressions by moving eyebrows
                if (Math.random() > 0.7) {
                  // More furrowed brow
                  eyebrows[0].setAttribute('d', 'M120 83 Q135 78 150 83');
                  eyebrows[1].setAttribute('d', 'M150 83 Q165 78 180 83');
                } else if (Math.random() > 0.4) {
                  // Slightly raised eyebrows for emphasis
                  eyebrows[0].setAttribute('d', 'M120 82 Q135 76 150 82');
                  eyebrows[1].setAttribute('d', 'M150 82 Q165 76 180 82');
                } else {
                  // Return to neutral-tense
                  eyebrows[0].setAttribute('d', 'M120 85 Q135 80 150 85');
                  eyebrows[1].setAttribute('d', 'M150 85 Q165 80 180 85');
                }
                
                // Continue animation while speaking
                setTimeout(animateEyebrows, 800 + Math.random() * 700);
              }
              
              // Reset judge to original state
              function resetJudge() {
                speaking = false;
                mouth.setAttribute('d', mouthTense); // Keep tense expression when not speaking
                speechBubble.style.display = 'none';
                speakButton.textContent = "Have Judge Announce Verdict";
                status.textContent = "Ready to speak";
                
                // Reset eyebrows to tense position
                const eyebrows = document.querySelectorAll('path[stroke="black"][stroke-width="2"]');
                eyebrows[0].setAttribute('d', 'M120 85 Q135 80 150 85');
                eyebrows[1].setAttribute('d', 'M150 85 Q165 80 180 85');
                
                // Reset gavel
                clearInterval(gavelInterval);
                gavelHead.setAttribute('transform', '');
                gavelHandle.setAttribute('transform', '');
              }
              
              // Improved gavel animation with the gavel in hand
              let gavelInterval;
              
              function animateGavel() {
                if (!speaking) return;
                
                // Rotate gavel for striking motion
                gavelHead.setAttribute('transform', 'rotate(-30 190 280)');
                gavelHandle.setAttribute('transform', 'rotate(-30 190 280)');
                
                setTimeout(() => {
                  // Return to normal position
                  gavelHead.setAttribute('transform', '');
                  gavelHandle.setAttribute('transform', '');
                  
                  // Optional: Add strike effect (visual flash)
                  const flash = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                  flash.setAttribute("x", "180");
                  flash.setAttribute("y", "265");
                  flash.setAttribute("width", "50");
                  flash.setAttribute("height", "20");
                  flash.setAttribute("fill", "white");
                  flash.setAttribute("opacity", "0.6");
                  document.getElementById("judgeSvg").appendChild(flash);
                  
                  // Remove flash effect after a short time
                  setTimeout(() => {
                    if (flash.parentNode) {
                      flash.parentNode.removeChild(flash);
                    }
                  }, 100);
                }, 200);
              }
              
              // Set initial tensed expression
              window.onload = function() {
                mouth.setAttribute('d', mouthTense);
              }
            </script>
            """
            
            # Inject HTML component into the Streamlit app
            components.html(judge_html, height=500)
            
            # Display enhanced analysis if available
            if 'enhanced_analysis' in st.session_state and st.session_state.enhanced_analysis:
                enhanced = st.session_state.enhanced_analysis
                st.subheader("Enhanced Analysis by GPT-4o")
                
                st.write("**AI-Enhanced Judgment Analysis:**")
                st.write(enhanced['outcome_analysis'])
                
                st.write("**Legal Principles Analysis:**")
                st.write(enhanced['legal_principles_analysis'])
                
                st.write("**Strategic Recommendations:**")
                st.write(enhanced['recommendations'])
        
        with pred_tab2:
            # Legal Analysis with detailed legal reasoning
            st.subheader("Applicable Legal Principles")
            for principle in prediction['legal_principles']:
                st.info(principle)
            
            st.subheader("Liability Determination")
            st.write(prediction['liability_determination'])
            
            st.subheader("Similar Precedents")
            for precedent in prediction['similar_precedents']:
                # Find matching case
                matching_case = next((case for case in st.session_state.similar_cases 
                                     if case['case_id'] == precedent['case_id']), None)
                if matching_case:
                    st.write(f"**{matching_case['title']}**")
                    st.caption(f"Case ID: {precedent['case_id']} | Relevance: {precedent['relevance']:.2f}")
        
        with pred_tab3:
            # Confidence Assessment
            st.subheader("Prediction Confidence Assessment")
            
            # Confidence visualization
            confidence = prediction['confidence']
            st.progress(confidence)
            
            st.write("**Confidence Analysis:**")
            st.write("The confidence score is calculated based on:")
            st.markdown("- Similarity with precedent cases\n- Consistency of outcomes in similar cases\n- Strength of legal principles application\n- Clarity of factual circumstances")
            
            st.write("**Interpretation:**")
            if confidence >= 0.7:
                st.success("This prediction has high confidence and is likely reliable.")
            elif confidence >= 0.5:
                st.warning("This prediction has moderate confidence, consider additional legal research.")
            else:
                st.error("This prediction has low confidence due to limited similar precedents or conflicting legal principles.")

        # Disclaimer
        st.warning("""
        **Disclaimer:** This prediction is based on machine learning analysis of similar cases and should not be 
        considered legal advice. The prediction is meant to provide insight into possible outcomes based on 
        historical data, but each case is unique and may have different outcomes in court.
        """)

# Sidebar for system information
st.sidebar.header("Settings")

# Check system information and dependencies
if not st.session_state.dependency_check:
    missing_libraries = []
    
    try:
        import PyPDF2
    except ImportError:
        missing_libraries.append("PyPDF2")
    
    try:
        import pdfplumber
    except ImportError:
        missing_libraries.append("pdfplumber")
        
    try:
        import faiss
    except ImportError:
        missing_libraries.append("FAISS")
        
    try:
        from transformers import AutoModel, AutoTokenizer
    except ImportError:
        missing_libraries.append("Transformers")
    
    st.session_state.dependency_check = True
    
    # Report missing dependencies in the sidebar
    if missing_libraries:
        st.sidebar.warning(f"Some optional dependencies are missing: {', '.join(missing_libraries)}")
        st.sidebar.info("The application will use fallback implementations where necessary.")
    else:
        st.sidebar.success("All dependencies are installed correctly.")

# Check if CUDA is available for GPU acceleration
if TORCH_AVAILABLE:
    device_info = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"
    st.sidebar.info(f"Running on: {device_info}")
else:
    st.sidebar.info("Running on: CPU (PyTorch not available)")

# Display OpenAI status
if OPENAI_AVAILABLE:
    st.sidebar.success("OpenAI API: Connected ✓")
else:
    st.sidebar.warning("OpenAI API: Not connected ✗")
    st.sidebar.info("Set the OPENAI_API_KEY environment variable for enhanced analysis capabilities.")
    
    # Add a button to input API key
    if st.sidebar.button("Add OpenAI API Key"):
        api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.sidebar.success("API Key set! Please refresh the page to use OpenAI features.")
            from utils.openai_integration import initialize_openai
            OPENAI_AVAILABLE = initialize_openai()