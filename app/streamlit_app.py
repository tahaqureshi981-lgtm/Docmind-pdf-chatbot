import os
import streamlit as st
import requests
import base64

API_URL = "https://docmind-pdf-chatbot-production.up.railway.app"

st.set_page_config(
    page_title="DocMind — AI PDF Reader",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
section[data-testid="stSidebar"] { display: none !important; }

/* ── Kill all default padding ── */
.main .block-container,
[data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
.main {
    height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
}
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockSeparator"] {
    gap: 0 !important;
    padding: 0 !important;
}
.stApp { background: #0f1117 !important; overflow: hidden !important; }

/* ── Three-column wrapper ── */
[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    height: 100vh !important;
    overflow: hidden !important;
    align-items: stretch !important;
}

/* ── Column 1 — Sidebar ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {
    background: #0f1117 !important;
    border-right: 1px solid #1e293b !important;
    height: 100vh !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding: 0 !important;
}

/* ── Column 2 — Chat ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    background: #0f1117 !important;
    border-right: 1px solid #1e293b !important;
    height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
}

/* ── Column 3 — PDF viewer ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {
    background: #0f1117 !important;
    height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
}

/* Make ALL Streamlit inner wrapper divs transparent across every column
   so the app's dark background shows through everywhere */
[data-testid="column"] > div,
[data-testid="column"] [data-testid="stVerticalBlock"],
[data-testid="column"] [data-testid="stVerticalBlock"] > div,
[data-testid="column"] [data-testid="stVerticalBlockSeparator"],
[data-testid="column"] .stMarkdown,
[data-testid="column"] .element-container,
[data-testid="column"] .stElementContainer {
    background: transparent !important;
}

/* ════════════════════════════
   SIDEBAR COMPONENTS
════════════════════════════ */
.sb-logo {
    padding: 20px 16px 16px;
    border-bottom: 1px solid #1e293b;
    display: flex; align-items: center; gap: 12px;
}
.sb-logo-mark {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem; font-weight: 800; color: white;
    letter-spacing: -0.03em; flex-shrink: 0;
    font-family: 'Inter', sans-serif;
}
.sb-logo-name {
    font-size: 1.25rem; font-weight: 800;
    color: #ffffff; letter-spacing: -0.03em;
    line-height: 1.1;
}
.sb-logo-tag {
    font-size: 0.65rem; font-weight: 600;
    color: #60a5fa; letter-spacing: 0.08em;
    text-transform: uppercase; margin-top: 3px;
}
.sb-section-lbl {
    font-size: 0.61rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #4b5563; padding: 14px 16px 6px; display: block;
}
.sb-doc-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 10px; border-radius: 8px;
    cursor: pointer; margin: 2px 8px; transition: background 0.15s;
}
.sb-doc-item:hover { background: #1e293b; }
.sb-doc-item.active { background: #1e3a5f; border: 1px solid rgba(59,130,246,0.4); }
.sb-doc-icon {
    width: 30px; height: 30px; background: #1e293b;
    border-radius: 7px; display: flex; align-items: center;
    justify-content: center; font-size: 14px; flex-shrink: 0;
}
.sb-doc-item.active .sb-doc-icon { background: #1d4ed8; }
.sb-doc-name {
    font-size: 0.79rem; font-weight: 500; color: #e5e7eb;
    white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; max-width: 158px;
}
.sb-doc-meta { font-size: 0.67rem; color: #6b7280; margin-top: 1px; }
.upgrade-card {
    background: linear-gradient(135deg, #1e3a5f, #1e1b4b);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 10px; padding: 13px; margin: 8px 12px 10px;
}
.upgrade-title { font-size: 0.78rem; font-weight: 600; color: #f9fafb; margin-bottom: 4px; }
.upgrade-desc  { font-size: 0.70rem; color: #6b7280; margin-bottom: 10px; line-height: 1.5; }
.upgrade-btn {
    background: white; color: #1e3a5f; border-radius: 6px;
    padding: 6px 12px; font-size: 0.74rem; font-weight: 600;
    width: 100%; text-align: center; cursor: pointer;
}
.user-profile {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px;
    margin: 4px 12px 14px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
}
.user-av {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 13px; font-weight: 700;
    color: white; flex-shrink: 0;
}
.user-name { font-size: 0.80rem; font-weight: 600; color: #e2e8f0; }
.user-meta { font-size: 0.68rem; color: #60a5fa; margin-top: 1px; font-weight: 500; }

/* ════════════════════════════
   CHAT PANEL COMPONENTS
════════════════════════════ */
.chat-header {
    padding: 14px 18px;
    border-bottom: 1px solid #1e293b;
    display: flex; align-items: center; gap: 12px;
    background: #0f1117; flex-shrink: 0;
}
.chat-header-av {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700; color: white; letter-spacing: 0.02em;
}
.chat-header-title { font-size: 0.92rem; font-weight: 600; color: #f1f5f9; }
.chat-header-sub   { font-size: 0.72rem; color: #64748b; margin-top: 1px; }
.chat-badge {
    margin-left: auto; background: #f0fdf4;
    border: 1px solid #bbf7d0; color: #16a34a;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.68rem; font-weight: 600; white-space: nowrap;
}
.ai-msg-row { display: flex; align-items: flex-start; gap: 9px; margin-bottom: 24px; }
.ai-av {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 8px; display: flex; align-items: center;
    justify-content: center; font-size: 0.58rem; font-weight: 700;
    color: white; letter-spacing: 0.02em; flex-shrink: 0; margin-top: 2px;
}
.ai-bubble {
    background: #1a1d2e; border: 1px solid #2a2d3e;
    border-radius: 3px 14px 14px 14px;
    padding: 11px 14px; max-width: 88%;
    font-size: 0.855rem; color: #cbd5e1; line-height: 1.65;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.user-msg-row { display: flex; justify-content: flex-end; margin-bottom: 24px; }
.user-bubble {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white; border-radius: 14px 3px 14px 14px;
    padding: 11px 15px; max-width: 82%;
    font-size: 0.855rem; line-height: 1.5;
    box-shadow: 0 3px 12px rgba(59,130,246,0.25);
}
.cite-wrap { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 9px; }
.cite-chip {
    display: flex; align-items: center; gap: 4px;
    background: #eff6ff; border: 1px solid #bfdbfe; color: #3b82f6;
    border-radius: 5px; padding: 2px 9px;
    font-size: 0.70rem; font-weight: 500;
}
.chat-input-wrap {
    border-top: 1px solid #1e293b;
    padding: 12px 16px 8px;
    background: #0f1117;
}
.chat-disclaimer {
    text-align: center; font-size: 0.63rem;
    color: #334155; margin-top: 5px; padding-bottom: 6px;
}
.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px 30px; text-align: center;
}
.empty-icon  { font-size: 3rem; margin-bottom: 14px; }
.empty-title { font-size: 0.96rem; font-weight: 600; color: #6b7280; margin-bottom: 8px; }
.empty-desc  { font-size: 0.83rem; color: #9ca3af; line-height: 1.65; }

/* ════════════════════════════
   PDF PANEL COMPONENTS
════════════════════════════ */
.pdf-toolbar {
    background: #0f1117; border-bottom: 1px solid #1e293b;
    padding: 10px 14px; display: flex; align-items: center; gap: 8px;
}
.pdf-fname {
    font-size: 0.80rem; font-weight: 600; color: #e2e8f0;
    white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; max-width: 220px;
}
.pdf-sub { font-size: 0.72rem; color: #475569; }

/* ════════════════════════════
   STREAMLIT WIDGET OVERRIDES
════════════════════════════ */

/* ── Text input — cursor + focus fix ── */
.stTextInput > div > div > input {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    caret-color: #3b82f6 !important;
    padding: 10px 14px !important;
    border: 1.5px solid #334155 !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    font-size: 0.875rem !important;
    height: 42px !important;
    line-height: 1.4 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input::placeholder { color: #94a3b8 !important; opacity: 1 !important; }
.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    outline: none !important;
    background: #1e293b !important;
}
.stTextInput > div > div,
.stTextInput > div { background: transparent !important; border: none !important; box-shadow: none !important; }
.stTextInput label { display: none !important; }

/* ── Primary button ── */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    height: 42px !important;
    white-space: nowrap !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
    transition: opacity 0.15s, transform 0.15s !important;
    letter-spacing: 0.01em !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; box-shadow: 0 4px 14px rgba(59,130,246,0.35) !important; }
.stButton > button:active { opacity: 0.8 !important; transform: translateY(0) !important; }

/* ── Clear button override ── */
.clear-btn .stButton > button {
    background: #f1f5f9 !important;
    color: #64748b !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 0.78rem !important;
    padding: 4px 14px !important;
    width: auto !important;
    box-shadow: none !important;
    height: 32px !important;
    font-weight: 500 !important;
    transform: none !important;
}
.clear-btn .stButton > button:hover {
    background: #1e293b !important;
    color: #94a3b8 !important;
    transform: none !important;
    opacity: 1 !important;
    box-shadow: none !important;
}
.stButton:last-of-type > button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 0.75rem !important;
    padding: 3px 12px !important;
    width: auto !important;
    box-shadow: none !important;
}

/* ── File uploader — dark theme for sidebar ── */
[data-testid="stFileUploaderDropzone"] {
    background: #1e293b !important;
    border: 2px dashed #3b82f6 !important;
    border-radius: 10px !important;
    padding: 16px !important;
    margin: 24px 12px 12px !important;
    cursor: pointer !important;
    text-align: center !important;
    transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #60a5fa !important;
    background: #172032 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] svg { stroke: #64748b !important; }
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFileData"]  { display: none !important; }
[data-testid="stFileUploader"] .stButton > button {
    background: #3b82f6 !important;
    font-size: 0.78rem !important;
    height: 30px !important;
    box-shadow: none !important;
}
[data-testid="stFileUploader"] .stButton > button:hover { transform: none !important; }

/* ── Scrollable message container ── */
[data-testid="stVerticalScrollableBlock"] {
    padding: 8px 20px 0 !important;
    background: #0f1117 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
[data-testid="stVerticalScrollableBlock"]::-webkit-scrollbar { width: 4px !important; }
[data-testid="stVerticalScrollableBlock"]::-webkit-scrollbar-thumb {
    background: #1e293b !important; border-radius: 10px !important;
}

/* ── Sidebar scrollbar ── */
[data-testid="column"]:nth-child(1)::-webkit-scrollbar { width: 3px !important; }
[data-testid="column"]:nth-child(1)::-webkit-scrollbar-thumb {
    background: #1e293b !important; border-radius: 10px !important;
}

/* ── Sidebar doc-list buttons (list-item look) ── */
[data-testid="column"]:nth-child(1) .stButton > button {
    background: transparent !important;
    color: #e5e7eb !important;
    border: none !important;
    border-radius: 8px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    height: auto !important;
    min-height: 40px !important;
    padding: 9px 10px !important;
    font-size: 0.79rem !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
    transform: none !important;
    width: 100% !important;
}
[data-testid="column"]:nth-child(1) .stButton > button:hover {
    background: #1e293b !important;
    transform: none !important;
    opacity: 1 !important;
    box-shadow: none !important;
}

/* File-uploader browse button — MORE specific, overrides the sidebar rule above */
[data-testid="column"]:nth-child(1) [data-testid="stFileUploader"] .stButton > button {
    background: #3b82f6 !important;
    color: white !important;
    font-size: 0.78rem !important;
    height: 30px !important;
    min-height: 30px !important;
    box-shadow: none !important;
    border-radius: 6px !important;
    justify-content: center !important;
    transform: none !important;
}
[data-testid="column"]:nth-child(1) [data-testid="stFileUploader"] .stButton > button:hover {
    background: #2563eb !important;
    opacity: 1 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Form wrapper (Enter-to-send) — strip Streamlit's default border ── */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}
/* Form submit button — same look as primary Send button */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    height: 42px !important;
    white-space: nowrap !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
    width: 100% !important;
    transition: opacity 0.15s !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    opacity: 0.88 !important;
    box-shadow: 0 4px 14px rgba(59,130,246,0.35) !important;
}

/* ── Sidebar doc-row: card look ── */
[data-testid="column"]:nth-child(1) [data-testid="stHorizontalBlock"] {
    background: #1e293b !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    gap: 4px !important;
    align-items: center !important;
    margin: 3px 8px !important;
    padding: 4px 8px !important;
}
/* Active doc card — blue border highlight */
[data-testid="stVerticalBlock"] > *:has(.doc-active-marker) + * [data-testid="stHorizontalBlock"] {
    border-color: rgba(59,130,246,0.6) !important;
    background: #1e3a5f !important;
}
.doc-chunks {
    font-size: 0.67rem !important;
    color: #6b7280 !important;
    margin: -4px 0 4px 10px !important;
    padding: 0 !important;
    line-height: 1 !important;
}

/* ── Delete (×) button in each doc row — more-specific selector wins over the general sidebar rule ── */
[data-testid="column"]:nth-child(1) [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) .stButton > button {
    background: transparent !important;
    color: #475569 !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    font-size: 0.80rem !important;
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 !important;
    justify-content: center !important;
    transform: none !important;
    letter-spacing: 0 !important;
    font-weight: 400 !important;
}
[data-testid="column"]:nth-child(1) [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) .stButton > button:hover {
    background: rgba(239,68,68,0.15) !important;
    color: #f87171 !important;
    border-color: #7f1d1d !important;
    opacity: 1 !important;
    transform: none !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #3b82f6 !important; }

/* ── Success/error messages ── */
.stSuccess, .stAlert, .stWarning, .stError { margin: 6px 12px !important; font-size: 0.82rem !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages"              not in st.session_state: st.session_state.messages              = []
if "active_doc"            not in st.session_state: st.session_state.active_doc            = None
if "pdf_bytes"             not in st.session_state: st.session_state.pdf_bytes             = None
if "pdf_name"              not in st.session_state: st.session_state.pdf_name              = None
if "upload_message"        not in st.session_state: st.session_state.upload_message        = None
if "delete_success"        not in st.session_state: st.session_state.delete_success        = None
if "last_processed_upload" not in st.session_state: st.session_state.last_processed_upload = None


def fetch_documents():
    try:
        r = requests.get(f"{API_URL}/documents", timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def show_pdf(pdf_bytes):
    b64 = base64.b64encode(pdf_bytes).decode()
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}#toolbar=0" '
        f'width="100%" height="100%" style="border:none;display:block;'
        f'min-height:calc(100vh - 56px);"></iframe>',
        unsafe_allow_html=True
    )


docs = fetch_documents()

# ── Three-column shell ─────────────────────────────────────────────────────────
sidebar_col, chat_col, pdf_col = st.columns([1.05, 1.85, 1.6])


# ══════════════════════════════════════════════════
# LEFT — Sidebar
# ══════════════════════════════════════════════════
with sidebar_col:
    # Logo
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-mark">D</div>
        <div>
            <div class="sb-logo-name">DocMind</div>
            <div class="sb-logo-tag">AI PDF Reader</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # File uploader (styled dark via CSS)
    uploaded_file = st.file_uploader(
        "Upload PDF", type=["pdf"], label_visibility="collapsed"
    )

    if uploaded_file and uploaded_file.name != st.session_state.last_processed_upload:
        already = any(d["filename"] == uploaded_file.name for d in docs)
        if not already:
            with st.spinner("Ingesting…"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    r = requests.post(f"{API_URL}/upload", files=files, timeout=60)
                    if r.status_code == 200:
                        st.session_state.upload_message = f"Ingested: {uploaded_file.name}"
                        docs = fetch_documents()
                except Exception as e:
                    st.error(str(e))
        st.session_state.last_processed_upload = uploaded_file.name
        st.session_state.pdf_bytes  = uploaded_file.getvalue()
        st.session_state.pdf_name   = uploaded_file.name
        st.session_state.active_doc = uploaded_file.name
        st.session_state.messages   = []
        st.rerun()

    # Show upload / delete feedback then clear
    if st.session_state.delete_success:
        st.success(f"Deleted: {st.session_state.delete_success}")
        st.session_state.delete_success = None
    elif st.session_state.upload_message:
        st.success(st.session_state.upload_message)
        st.session_state.upload_message = None

    # Document list
    if docs:
        st.markdown('<hr style="border:none;border-top:1px solid #1e293b;margin:8px 0 0">', unsafe_allow_html=True)
        st.markdown('<span class="sb-section-lbl">My Documents</span>', unsafe_allow_html=True)
        for doc in docs:
            short = doc["filename"][:20] + "…" if len(doc["filename"]) > 20 else doc["filename"]
            is_active = st.session_state.active_doc == doc["filename"]
            st.markdown(
                '<div class="doc-active-marker"></div>' if is_active else '<div class="doc-inactive-marker"></div>',
                unsafe_allow_html=True
            )
            name_col, del_col = st.columns([5, 1])
            with name_col:
                if st.button(short, key=f"doc_{doc['pdf_hash']}", use_container_width=True):
                    st.session_state.active_doc = doc["filename"]
                    pdf_path = f"data/{doc['filename']}"
                    try:
                        with open(pdf_path, "rb") as f:
                            st.session_state.pdf_bytes = f.read()
                        st.session_state.pdf_name = doc["filename"]
                    except Exception:
                        pass
                    st.rerun()
            with del_col:
                if st.button("×", key=f"del_{doc['pdf_hash']}", use_container_width=True):
                    deleted_name = doc["filename"]
                    was_active = st.session_state.active_doc == deleted_name
                    try:
                        requests.delete(f"{API_URL}/documents/{doc['pdf_hash']}", timeout=10)
                    except Exception:
                        pass
                    pdf_path = os.path.join("data", deleted_name)
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    st.session_state.messages = []
                    st.session_state.upload_message = None
                    st.session_state.delete_success = deleted_name
                    # Allow re-uploading the same file after deletion
                    if st.session_state.last_processed_upload == deleted_name:
                        st.session_state.last_processed_upload = None
                    if was_active:
                        st.session_state.active_doc = None
                        st.session_state.pdf_bytes = None
                        st.session_state.pdf_name = None
                        # Auto-select first remaining doc
                        remaining = fetch_documents()
                        if remaining:
                            first = remaining[0]
                            st.session_state.active_doc = first["filename"]
                            st.session_state.pdf_name = first["filename"]
                            try:
                                with open(f"data/{first['filename']}", "rb") as f:
                                    st.session_state.pdf_bytes = f.read()
                            except Exception:
                                pass
                    st.rerun()

    # Bottom — upgrade + user
    st.markdown("""
    <div style="height:1px;background:#1e293b;margin:12px 0 0"></div>
    <div class="upgrade-card">
        <div class="upgrade-title">Upgrade to Pro</div>
        <div class="upgrade-desc">Unlock unlimited uploads, advanced search, and priority AI.</div>
        <div class="upgrade-btn">Upgrade Now</div>
    </div>
    <div class="user-profile">
        <div class="user-av">T</div>
        <div>
            <div class="user-name">Taha Qureshi</div>
            <div class="user-meta">AI/ML Portfolio</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# CENTER — Chat
# ══════════════════════════════════════════════════
with chat_col:
    # Header
    st.markdown("""
    <div class="chat-header">
        <div class="chat-header-av">AI</div>
        <div>
            <div class="chat-header-title">DocMind Assistant</div>
            <div class="chat-header-sub">Powered by Llama 3.1 + RAG</div>
        </div>
        <div class="chat-badge">&#9679; Online</div>
    </div>
    """, unsafe_allow_html=True)

    # Scrollable message area (fixed height, scrollable)
    msgs_box = st.container(height=540, border=False)
    with msgs_box:
        if not st.session_state.messages:
            if not st.session_state.active_doc:
                body = (
                    "Hi there! I'm <strong style='color:#93c5fd'>DocMind</strong>, your AI document assistant.<br><br>"
                    "Upload a PDF to get started — I'll answer questions strictly from the document content "
                    "and show you exactly where I found the information."
                )
            else:
                body = (
                    f"<strong style='color:#93c5fd'>{st.session_state.active_doc}</strong> is ready.<br><br>"
                    "Ask me anything about this document and I'll answer from its content."
                )
            st.markdown(f"""
            <div class="ai-msg-row" style="margin-top:22px">
                <div class="ai-av">AI</div>
                <div class="ai-bubble">{body}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="user-msg-row">
                        <div class="user-bubble">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    sources_html = ""
                    if msg.get("sources"):
                        sources_html = '<div class="cite-wrap">' + "".join(
                            f'<span class="cite-chip">Source {i+1} · chunk {s["chunk_index"]}</span>'
                            for i, s in enumerate(msg["sources"])
                        ) + '</div>'
                    st.markdown(f"""
                    <div class="ai-msg-row">
                        <div class="ai-av">AI</div>
                        <div class="ai-bubble">{msg["content"]}{sources_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # Input row — wrapped in form so Enter key submits
    st.markdown('<div class="chat-input-wrap">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True, border=False):
        inp_col, btn_col = st.columns([5, 1])
        with inp_col:
            question = st.text_input(
                "q", placeholder="Ask anything about your document…",
                label_visibility="collapsed"
            )
        with btn_col:
            send = st.form_submit_button("Send ➤", use_container_width=True)

    # Clear button (outside form — secondary style)
    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("Clear chat", key="clear_btn"):
        st.session_state.messages = []
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="chat-disclaimer">
        Answers are generated strictly from uploaded document content.
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Handle send
    if send and question.strip():
        if not st.session_state.active_doc:
            st.warning("Please select or upload a PDF first.")
        else:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Thinking…"):
                try:
                    payload = {
                        "question": question,
                        "filename_filter": st.session_state.active_doc,
                        "n_chunks": 3,
                        "chat_history": [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages[-6:]
                            if m["role"] in ("user", "assistant")
                        ]
                    }
                    r = requests.post(f"{API_URL}/chat", json=payload, timeout=30)
                    if r.status_code == 200:
                        result = r.json()
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": result["sources"]
                        })
                    else:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ Error: {r.text}",
                            "sources": []
                        })
                except Exception as e:
                    st.error(str(e))
            st.rerun()


# ══════════════════════════════════════════════════
# RIGHT — PDF Viewer
# ══════════════════════════════════════════════════
with pdf_col:
    if st.session_state.pdf_bytes:
        short = (
            st.session_state.pdf_name[:34] + "…"
            if st.session_state.pdf_name and len(st.session_state.pdf_name) > 34
            else st.session_state.pdf_name
        )
        st.markdown(f"""
        <div class="pdf-toolbar">
            <span style="font-size:1.1rem;flex-shrink:0">📄</span>
            <div style="min-width:0">
                <div class="pdf-fname">{short}</div>
                <div class="pdf-sub">Document Preview</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        show_pdf(st.session_state.pdf_bytes)
    else:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:100vh;
                    background:#0f1117;text-align:center;padding:40px">
            <svg width="52" height="64" viewBox="0 0 52 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-bottom:18px;opacity:0.35">
                <path d="M32 2H6C3.8 2 2 3.8 2 6V58C2 60.2 3.8 62 6 62H46C48.2 62 50 60.2 50 58V20L32 2Z" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M32 2V20H50" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 36H38M14 44H28" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <div style="font-size:1rem;font-weight:600;color:#94a3b8;margin-bottom:8px">
                No document selected
            </div>
            <div style="font-size:0.83rem;line-height:1.65;color:#475569">
                Upload a PDF from the sidebar<br>to preview it here
            </div>
        </div>
        """, unsafe_allow_html=True)