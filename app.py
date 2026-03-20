# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import docx
import PyPDF2
import re
from collections import Counter
import io
from deep_translator import GoogleTranslator
import google.generativeai as genai

# ---------------------------------------------------------
# Section 1: ระบบจัดการ 2 ภาษา (Language Mapping)
# ---------------------------------------------------------
LANG_TEXTS = {
    "TH": {
        "title": "📝 ผู้ช่วยวิเคราะห์คำศัพท์และสรุปใจความ",
        "desc": "เครื่องมือช่วยนักแปล: วิเคราะห์ศัพท์, สรุปเนื้อหาด้วย AI และประเมินเวลาทำงาน",
        "sidebar_settings": "⚙️ การตั้งค่า",
        "api_key_label": "ใส่ Gemini API Key (เพื่อใช้ AI Summary)",
        "speed_label": "ความเร็วการแปล (คำต่อชั่วโมง)",
        "upload_label": "เลือกไฟล์เอกสาร (.txt, .docx, .pdf)",
        "summary_title": "🤖 สรุปเนื้อหาโดย AI (Gemini)",
        "time_title": "⏳ การประเมินเวลาทำงาน (Estimate)",
        "total_words": "จำนวนคำทั้งหมด:",
        "est_time": "เวลาที่คาดว่าต้องใช้:",
        "processing": "กำลังประมวลผล...",
        "chart_title": "📊 Top 30 คำศัพท์ที่ใช้บ่อย",
        "table_title": "📋 Glossary & Collocations",
        "btn_download": "📥 ดาวน์โหลด Glossary (.xlsx)",
        "ai_warn": "กรุณาใส่ API Key ในแถบด้านข้างเพื่อใช้งาน AI Summary",
        "col_word": "คำศัพท์", "col_freq": "ความถี่", "col_trans": "คำแปล", "col_context": "บริบท", "col_collocate": "คำที่ใช้คู่กัน"
    },
    "EN": {
        "title": "📝 Vocab Analyzer & AI Summarizer",
        "desc": "Translator Toolkit: Vocab Analysis, AI Summary, and Time Estimation",
        "sidebar_settings": "⚙️ Settings",
        "api_key_label": "Enter Gemini API Key (for AI Summary)",
        "speed_label": "Translation Speed (Words/Hour)",
        "upload_label": "Upload document (.txt, .docx, .pdf)",
        "summary_title": "🤖 AI Summary (Gemini)",
        "time_title": "⏳ Workload Estimation",
        "total_words": "Total Word Count:",
        "est_time": "Estimated Time:",
        "processing": "Processing...",
        "chart_title": "📊 Top 30 Most Frequent Words",
        "table_title": "📋 Glossary & Collocations",
        "btn_download": "📥 Download Glossary (.xlsx)",
        "ai_warn": "Please enter API Key in the sidebar to enable AI Summary",
        "col_word": "Word", "col_freq": "Freq", "col_trans": "Translation", "col_context": "Context", "col_collocate": "Collocates"
    }
}

# ---------------------------------------------------------
# Section 2: ฟังก์ชันคำนวณและประมวลผล
# ---------------------------------------------------------
STOPWORDS = set(["i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "them", "a", "an", "the", "and", "but", "if", "or", "as", "of", "at", "by", "for", "with", "about", "to", "from", "in", "on", "is", "are", "was", "were", "be", "been", "do", "does", "did", "can", "will", "should", "not", "this", "that"])

def get_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8")
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return '\n'.join([p.text for p in doc.paragraphs])
    elif uploaded_file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        return '\n'.join([page.extract_text() for page in reader.pages])
    return ""

def ask_gemini(api_key, text, lang):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Summarize the following text for a translator. Focus on the main topic, tone, and key terminology. Answer in {'Thai' if lang=='TH' else 'English'}:\n\n{text[:10000]}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------------------------------------------------
# Section 3: UI Implementation
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Translator Tool", layout="wide")

with st.sidebar:
    ui_lang = st.radio("Language / ภาษา", ("ไทย", "English"))
    lang_key = "TH" if ui_lang == "ไทย" else "EN"
    txt = LANG_TEXTS[lang_key]
    
    st.markdown("---")
    st.subheader(txt["sidebar_settings"])
    api_key = st.text_input(txt["api_key_label"], type="password")
    trans_speed = st.slider(txt["speed_label"], 100, 1000, 250)

st.title(txt["title"])
st.write(txt["desc"])

uploaded_file = st.file_uploader(txt["upload_label"], type=["txt", "docx", "pdf"])

if uploaded_file:
    full_text = get_text_from_file(uploaded_file)
    
    if full_text:
        # 1. คำนวณจำนวนคำและเวลา (Time Estimate)
        all_words_raw = re.findall(r'\b[a-z]+\b', full_text.lower())
        total_word_count = len(all_words_raw)
        est_hours = total_word_count / trans_speed
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**{txt['total_words']}** {total_word_count:,} words")
        with col2:
            st.success(f"**{txt['est_time']}** {est_hours:.1f} hours ({est_hours/8:.1f} working days)")

        # 2. AI Summary
        st.subheader(txt["summary_title"])
        if api_key:
            with st.spinner(txt["processing"]):
                summary = ask_gemini(api_key, full_text, lang_key)
                st.write(summary)
        else:
            st.warning(txt["ai_warn"])

        st.markdown("---")

        # 3. วิเคราะห์คำศัพท์ (เหมือนเดิม)
        filtered_words = [w for w in all_words_raw if w not in STOPWORDS and len(w) > 1]
        word_counts = Counter(filtered_words)
        top_30 = word_counts.most_common(30)
        
        if top_30:
            df = pd.DataFrame(top_30, columns=[txt["col_word"], txt["col_freq"]])
            
            # แปลและดึง Context/Collocates (ใช้ Logic เดิม)
            with st.spinner(txt["processing"]):
                translator = GoogleTranslator(source='en', target='th' if lang_key=="TH" else 'en')
                df[txt["col_trans"]] = [translator.translate(w) for w in df[txt["col_word"]]]
                
                sentences = re.split(r'(?<=[.!?])\s+', full_text.replace('\n', ' '))
                df[txt["col_context"]] = [next((s.strip() for s in sentences if re.search(rf'\b{w}\b', s, re.I)), "-") for w in df[txt["col_word"]]]
                
                # Collocates logic
                def quick_collocate(target, all_w):
                    near = []
                    for i, v in enumerate(all_w):
                        if v == target:
                            near.extend(all_w[max(0, i-2):i] + all_w[i+1:i+3])
                    res = [c[0] for c in Counter([n for n in near if n != target and n not in STOPWORDS]).most_common(2)]
                    return ", ".join(res) if res else "-"
                
                df[txt["col_collocate"]] = [quick_collocate(w, all_words_raw) for w in df[txt["col_word"]]]

            # แสดงผล
            st.subheader(txt["chart_title"])
            st.bar_chart(df.set_index(txt["col_word"])[txt["col_freq"]])
            
            st.subheader(txt["table_title"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Glossary')
            st.download_button(txt["btn_download"], buffer.getvalue(), "glossary.xlsx")
