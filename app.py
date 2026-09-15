import streamlit as st
from groq import Groq
import pypdf
import docx
import time

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="MockMaster AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CLOUD-SAFE CLEAN CSS (NO SCROLL-LOCKING CONFLICTS)
# =========================================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');

* {
    font-family: 'DM Sans', sans-serif;
}

/* Background Color */
.stApp {
    background-color: #070B14;
    color: #E2E8F0;
}

.block-container {
    max-width: 1100px;
    padding-top: 1.5rem;
    padding-bottom: 6rem;
}

#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #0B1120;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

section[data-testid="stSidebar"] h3 {
    font-family: 'Space Grotesk', sans-serif;
    color: #F8FAFC;
}

div[role="radiogroup"] {
    gap: 6px;
}

div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 8px 12px;
}

/* HERO BRAND */
.brand-container {
    padding-bottom: 16px;
    margin-bottom: 18px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-kicker {
    display: inline-block;
    padding: 4px 10px;
    margin-bottom: 8px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-radius: 999px;
    color: #A5B4FC;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
}

.brand-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -1.5px;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(120deg, #F8FAFC 10%, #A5B4FC 50%, #38BDF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.brand-subtitle {
    color: #94A3B8;
    font-size: 0.96rem;
    margin-top: 6px;
    line-height: 1.5;
}

/* SECTION HEADER */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0 16px 0;
}

.section-icon {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(129, 140, 248, 0.25);
    font-size: 1.25rem;
}

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #F8FAFC;
    margin: 0;
}

/* STYLING FOR STREAMLIT BORDERED CONTAINERS */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    margin-bottom: 16px !important;
    padding: 6px !important;
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

.card-title-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.text-blue { color: #60A5FA; }
.text-green { color: #34D399; }
.text-amber { color: #FBBF24; }
.text-red { color: #F87171; }
.text-purple { color: #C084FC; }

/* PROGRESS */
.progress-wrapper {
    margin: 0 0 16px 0;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    color: #94A3B8;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 5px;
}

.progress-track {
    height: 6px;
    width: 100%;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #6366F1, #38BDF8);
}

/* BUTTONS */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #4F46E5 0%, #2563EB 100%);
    color: white;
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-weight: 600;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""
if "cached_steps" not in st.session_state:
    st.session_state.cached_steps = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_step" not in st.session_state:
    st.session_state.active_step = 0

STEPS_LIST = [
    ("1. Candidate Overview", "📌"),
    ("2. Core Skills", "🛠️"),
    ("3. Missing Signals", "⚠️"),
    ("4. Strengths vs Gaps", "⚖️"),
    ("5. Interview Red Flags", "🛡️"),
    ("6. Question Bank", "❓"),
    ("7. Top 5 Priorities", "🎯"),
    ("8. STAR Answer Blueprint", "⭐"),
    ("9. Curveball Coach", "💡"),
    ("10. Readiness & Advice", "🏆"),
    ("11. Mock Interview Simulator", "💬")
]

# =========================================================
# GROQ CONFIG & CALLER
# =========================================================
GROQ_MODEL = "openai/gpt-oss-120b"
groq_key = st.secrets.get("GROQ_API_KEY", "")

client = Groq(api_key=groq_key, timeout=35.0) if groq_key else None

def call_groq_robust(prompt: str, retries: int = 3) -> tuple[str, bool]:
    if not groq_key:
        return ("⚠️ Groq API Key missing. Please provide it in secrets or sidebar.", False)
    if client is None:
        return ("❌ Groq client could not be initialized.", False)

    system_prompt = (
        "You are an expert executive interview mentor. "
        "RULES: "
        "1. Use simple, conversational, everyday English. No complex jargon. "
        "2. Do NOT output markdown asterisks (no **text**). Use clean HTML <b>text</b> instead. "
        "3. Write short, clear, complete sentences. "
        "4. Keep answers brief and immediately scannable."
    )

    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=1500,
                reasoning_effort="low",
                include_reasoning=False,
            )
            if response.choices and response.choices[0].message.content:
                clean_text = (
                    response.choices[0].message.content
                    .replace("**", "")
                    .replace("###", "")
                    .strip()
                )
                return (clean_text, True)
            else:
                last_error = "Received empty response from server."
        except Exception as e:
            err_str = str(e).lower()
            last_error = str(e)
            if "connection" in err_str or "timeout" in err_str or "503" in err_str:
                time.sleep(1.5 * attempt)
                continue
            else:
                break

    return (f"Connection unstable: {last_error}", False)

def parse_file(uploaded_file) -> str:
    try:
        if uploaded_file.name.endswith(".pdf"):
            reader = pypdf.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        elif uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        else:
            return uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as err:
        st.error(f"Error reading file: {err}")
        return ""

def format_clean_html(content: str) -> str:
    return content.replace("\n", "<br>")

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""<div style="padding: 0 0 14px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 14px;">
        <div style="font-family: 'Space Grotesk'; font-size: 1.25rem; font-weight: 700; color: #F8FAFC;">
            🎯 MockMaster AI
        </div>
        <div style="color: #64748B; font-size: 0.8rem; margin-top: 4px;">
            Interview preparation workspace
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("### ⚡ Interview Pipeline")
    st.caption("Choose a stage to continue.")

    step_names = [f"{icon} {name}" for name, icon in STEPS_LIST]
    selected_step_index = st.radio(
        "Stages Menu",
        options=range(len(STEPS_LIST)),
        format_func=lambda i: step_names[i],
        index=st.session_state.active_step,
        label_visibility="collapsed"
    )
    st.session_state.active_step = selected_step_index

    st.markdown("---")
    if not groq_key:
        groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    if st.button("↺  Reset All Data", use_container_width=True):
        st.session_state.cv_text = ""
        st.session_state.cached_steps = {}
        st.session_state.chat_history = []
        st.session_state.active_step = 0
        st.rerun()

# =========================================================
# HERO HEADER
# =========================================================
st.markdown("""<div class="brand-container">
    <div class="brand-kicker">✦ AI-POWERED INTERVIEW COACH</div>
    <h1 class="brand-title">MockMaster AI</h1>
    <div class="brand-subtitle">
        Turn your CV into a complete interview preparation plan.
        Find your strengths, prepare better answers, and practice with an AI coach.
    </div>
</div>""", unsafe_allow_html=True)

# =========================================================
# RESUME SECTION
# =========================================================
with st.expander("📄  Upload or Paste Your Resume", expanded=not bool(st.session_state.cv_text)):
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### 📁 Upload your CV")
        uploaded_file = st.file_uploader("PDF, DOCX or TXT", type=["pdf", "docx", "txt"], label_visibility="collapsed")
        st.caption("Supported formats: PDF, DOCX, TXT")

    with col2:
        st.markdown("#### ✍️ Paste your resume")
        cv_text_area = st.text_area(
            "Resume text",
            height=135,
            value=st.session_state.cv_text,
            placeholder="Paste your CV text here...",
            label_visibility="collapsed"
        )

    if st.button("💾  Save Resume & Start Analysis", use_container_width=True):
        final_cv = ""
        if uploaded_file:
            final_cv = parse_file(uploaded_file)
        elif cv_text_area.strip():
            final_cv = cv_text_area.strip()

        if not final_cv.strip():
            st.error("Please provide your resume text.")
        else:
            st.session_state.cv_text = final_cv.strip()
            st.session_state.cached_steps = {}
            st.success("Resume saved successfully. Choose an interview stage from the sidebar.")
            st.rerun()

if not st.session_state.cv_text:
    with st.container(border=True):
        st.markdown('<div class="card-title-text text-blue">🚀 Ready to begin?</div>', unsafe_allow_html=True)
        st.write("Upload your resume or paste your CV above. MockMaster AI will turn it into a structured interview preparation workflow.")
    st.stop()

# =========================================================
# PROGRESS & SECTION TITLE
# =========================================================
curr_step = st.session_state.active_step
step_title, step_icon = STEPS_LIST[curr_step]
cv_context = st.session_state.cv_text[:3500]

progress = int(((curr_step + 1) / len(STEPS_LIST)) * 100)
st.markdown(f"""<div class="progress-wrapper">
    <div class="progress-info">
        <span>Interview preparation progress</span>
        <span>Step {curr_step + 1} of {len(STEPS_LIST)}</span>
    </div>
    <div class="progress-track">
        <div class="progress-fill" style="width:{progress}%"></div>
    </div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="section-header">
    <div class="section-icon">{step_icon}</div>
    <div>
        <div class="section-title">{step_title}</div>
        <div style="color: #64748B; font-size: 0.85rem;">AI-powered interview analysis</div>
    </div>
</div>""", unsafe_allow_html=True)

def handle_step_generation(step_key: str, button_label: str, prompt: str):
    if step_key not in st.session_state.cached_steps:
        if st.button(button_label, key=f"btn_{step_key}"):
            with st.spinner("Analyzing with AI coach..."):
                content, success = call_groq_robust(prompt)
                if success:
                    st.session_state.cached_steps[step_key] = content
                    st.rerun()
                else:
                    st.warning("⚠️ Internet connection was unstable.")
                    st.error(content)
                    if st.button("🔄 Try Again Now", key=f"retry_{step_key}"):
                        st.rerun()
    return st.session_state.cached_steps.get(step_key, None)

# =========================================================
# PIPELINE STAGES (USING NATIVE CONTAINERS)
# =========================================================

# STEP 1
if curr_step == 0:
    prompt = (
        f"Read this CV and describe the candidate in simple, everyday English.\n"
        f"Write 3 short paragraphs:\n"
        f"1. Who this person is and their main expertise.\n"
        f"2. Their top 2 real projects and what they built.\n"
        f"3. Their biggest single achievement in plain words.\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_1", "✨ Generate Candidate Overview", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-blue">📌 Candidate Snapshot</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 2
elif curr_step == 1:
    prompt = (
        f"List the candidate's skills from this CV in very simple sentences:\n"
        f"- Main Coding Languages: (one clear sentence)\n"
        f"- Important Libraries & Tools: (one clear sentence)\n"
        f"- Practical Skills: (2 simple sentences on what they actually build)\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_2", "🛠️ Extract Core Skills", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-green">🛠️ Core Capabilities</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 3
elif curr_step == 2:
    prompt = (
        f"Tell this candidate what is missing or vague in their CV using simple English:\n"
        f"1. Where did they forget to provide concrete numbers or percentages?\n"
        f"2. Which project lacks proof of real-world scale or users?\n"
        f"3. What is one quick update they should make right now?\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_3", "🔎 Audit Missing Information", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-amber">⚠️ Things to Clarify</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 4
elif curr_step == 3:
    prompt = (
        f"Analyze this CV into simple sentences:\n"
        f"Part 1: 3 short sentences about what makes this candidate strong.\n"
        f"Part 2: 3 short sentences about what is weak or missing.\n"
        f"Separate the two parts using the exact text: 'SPLIT_HERE'.\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_4", "⚖️ Analyze Strengths & Gaps", prompt)
    if result:
        parts = result.split("SPLIT_HERE")
        str_content = parts[0].strip()
        gap_content = parts[1].strip() if len(parts) > 1 else "No critical weak spots found."

        col_s, col_w = st.columns(2, gap="large")
        with col_s:
            with st.container(border=True):
                st.markdown('<div class="card-title-text text-green">🟢 Key Strengths</div>', unsafe_allow_html=True)
                st.markdown(format_clean_html(str_content), unsafe_allow_html=True)
        with col_w:
            with st.container(border=True):
                st.markdown('<div class="card-title-text text-red">🔴 Key Gaps & Weaknesses</div>', unsafe_allow_html=True)
                st.markdown(format_clean_html(gap_content), unsafe_allow_html=True)

# STEP 5
elif curr_step == 4:
    prompt = (
        f"Act as a critical interviewer. Identify:\n"
        f"- 2 immediate doubts or red flags triggered by this CV.\n"
        f"- For each doubt, give a 1-sentence safe defense the candidate can say.\n"
        f"Keep it very simple and conversational.\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_5", "🛡️ Detect Interview Red Flags", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-red">🛡️ Interview Doubts & Defenses</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 6
elif curr_step == 5:
    prompt = (
        f"Write 5 realistic, concise interview questions based on this CV:\n"
        f"- 2 on technical coding or tools\n"
        f"- 2 on project implementation details\n"
        f"- 1 on teamwork and communication\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_6", "❓ Generate Interview Questions", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-blue">❓ Likely Interview Questions</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 7
elif curr_step == 6:
    prompt = (
        f"Pick the 5 most guaranteed questions for this candidate.\n"
        f"Under each, write one simple sentence on what the interviewer secretly wants to hear.\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_7", "🎯 Prioritize Top Questions", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-purple">🎯 Guaranteed Questions</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 8
elif curr_step == 7:
    prompt = (
        f"Pick the candidate's biggest project and write a clean STAR answer for: 'Tell me about a challenging project you built.'\n"
        f"- Situation: (1 short sentence)\n"
        f"- Task: (1 short sentence)\n"
        f"- Action: (2 short sentences)\n"
        f"- Result: (1 sentence with numbers or clear impact)\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_8", "⭐ Generate STAR Model Answer", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-green">⭐ STAR Answer Blueprint</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 9
elif curr_step == 8:
    prompt = (
        f"Give 2 difficult curveball questions (e.g., handling failure or technical weaknesses).\n"
        f"Provide a natural, 2-sentence confident answer for each.\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_9", "💡 Prepare Curveball Coach", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-amber">💡 Tricky Questions & Answers</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 10
elif curr_step == 9:
    prompt = (
        f"Analyze this CV and give:\n"
        f"1. Score: Readiness score out of 100 with one short sentence.\n"
        f"2. Three quick DOs (things to emphasize in the interview).\n"
        f"3. Three quick DONTs (things to avoid mentioning).\n"
        f"Use short, simple sentences.\n\nCV:\n{cv_context}"
    )
    result = handle_step_generation("step_10", "🏆 Calculate Readiness & Tips", prompt)
    if result:
        with st.container(border=True):
            st.markdown('<div class="card-title-text text-purple">🏆 Score & Core Advice</div>', unsafe_allow_html=True)
            st.markdown(format_clean_html(result), unsafe_allow_html=True)

# STEP 11
elif curr_step == 10:
    with st.container(border=True):
        st.markdown('<div class="card-title-text text-blue">💬 AI Mock Interview Simulator</div>', unsafe_allow_html=True)
        st.write("Type your draft answer to an interview question. MockMaster AI will score your answer from <b>1 to 10</b>, show what to improve, and give you a stronger version.", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_resp = st.chat_input("Type your interview answer here...")
    if user_resp:
        st.session_state.chat_history.append({"role": "user", "content": user_resp})
        with st.chat_message("user"):
            st.markdown(user_resp)

        with st.chat_message("assistant"):
            with st.spinner("Your AI coach is reviewing the answer..."):
                sim_prompt = (
                    f"A candidate practicing an interview says: '{user_resp}'.\n"
                    f"CV context: {cv_context[:1000]}\n"
                    f"Provide:\n"
                    f"1. Quick Score (1-10)\n"
                    f"2. 1 Good point & 1 Thing to improve (short bullets)\n"
                    f"3. Refined Version: A clean 2-sentence high-impact answer."
                )
                critique, ok = call_groq_robust(sim_prompt)
                if ok:
                    st.markdown(critique)
                    st.session_state.chat_history.append({"role": "assistant", "content": critique})
                else:
                    st.error(critique)
