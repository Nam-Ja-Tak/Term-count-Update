import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import docx
import PyPDF2
import re
from collections import Counter
import io
from deep_translator import GoogleTranslator

# ---------------------------------------------------------
# Section 1: การตั้งค่าภาษา UI
# ---------------------------------------------------------
LANG_TEXTS = {
    "TH": {
        "title": "📝 เครื่องมือวิเคราะห์งานแปล (Offline Version)",
        "desc": "วิเคราะห์คำศัพท์, สรุปใจความสำคัญด้วยสถิติ และประเมินเวลาทำงาน",
        "sidebar_settings": "⚙️ ตั้งค่าการประเมินเวลา",
        "speed_label": "ความเร็วการแปลของคุณ (คำต่อชั่วโมง)",
        "upload_label": "อัปโหลดไฟล์ (.txt, .docx, .pdf)",
        "summary_title": "📌 สรุปใจความสำคัญ (ดึงจากประโยคที่มีคะแนนสูงสุด)",
        "time_title": "⏳ ประเมินเวลาทำงาน",
        "total_words": "จำนวนคำทั้งหมด:",
        "est_time": "เวลาที่คาดว่าต้องใช้:",
        "chart_title": "📊 Top 30 คำศัพท์ที่ใช้บ่อย",
        "table_title": "📋 Glossary & Collocations",
        "btn_download": "📥 ดาวน์โหลด Glossary (.xlsx)",
        "col_word": "คำศัพท์", "col_freq": "ความถี่", "col_trans": "คำแปล", "col_context": "ประโยคตัวอย่าง", "col_collocate": "คำคู่กัน"
    },
    "EN": {
        "title": "📝 Translation Analyzer (Offline)",
        "desc": "Analyze vocab, statistical summary, and work estimation.",
        "sidebar_settings": "⚙️ Estimation Settings",
        "speed_label": "Your Translation Speed (Words/Hour)",
        "upload_label": "Upload file (.txt, .docx, .pdf)",
        "summary_title": "📌 Key Sentence Summary",
        "time_title": "⏳ Workload Estimation",
        "total_words": "Total Words:",
        "est_time": "Estimated Time:",
        "chart_title": "📊 Top 30 Most Frequent Words",
        "table_title": "📋 Glossary & Collocations",
        "btn_download": "📥 Download Glossary (.xlsx)",
        "col_word": "Word", "col_freq": "Freq", "col_trans": "Translation", "col_context": "Context", "col_collocate": "Collocates"
    }
}

# ---------------------------------------------------------
# Section 2: ฟังก์ชันสรุปใจความ (แบบไม่ต้องใช้ AI)
# ---------------------------------------------------------
def statistical_summary(text, top_words_dict, num_sentences=3):
    """สรุปบทความโดยการดึงประโยคที่มี 'คำสำคัญ' ปรากฏอยู่มากที่สุด"""
    # 1. แยกข้อความออกเป็นประโยค
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    score_card = {}

    for i, sentence in enumerate(sentences):
        # 2. ให้คะแนนแต่ละประโยคตามความถี่ของคำที่อยู่ในประโยคนั้น
        for word, freq in top_words_dict.items():
            if word.lower() in sentence.lower():
                score_card[i] = score_card.get(i, 0) + freq
    
    # 3. เรียงลำดับประโยคที่คะแนนสูงสุด
    top_indices = sorted(score_card, key=score_card.get, reverse=True)[:num_sentences]
    top_indices.sort() # เรียงกลับตามลำดับประโยคที่เกิดก่อนหลัง
    
    result = [sentences[i].strip() for i in top_indices]
    return " ... ".join(result) if result else "ไม่สามารถสรุปได้"

# ---------------------------------------------------------
# Section 3: ฟังก์ชันอ่านไฟล์
# ---------------------------------------------------------
def get_text_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            return '\n'.join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded_file)
            return '\n'.join([page.extract_text() for page in reader.pages])
    except:
        return ""
    return ""

# ---------------------------------------------------------
# Section 4: Main UI
# ---------------------------------------------------------
st.set_page_config(page_title="Translator Toolkit", layout="wide")

STOPWORDS = set(["i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "them", "a", "an", "the", "and", "but", "if", "or", "as", "of", "at", "by", "for", "with", "about", "to", "from", "in", "on", "is", "are", "was", "were", "be", "been", "do", "does", "did", "can", "will", "should", "not", "this", "that"])

with st.sidebar:
    ui_lang = st.radio("Language / ภาษา", ("ไทย", "English"))
    lang_key = "TH" if ui_lang == "ไทย" else "EN"
    txt = LANG_TEXTS[lang_key]
    st.markdown("---")
    st.subheader(txt["sidebar_settings"])
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
        
        c1, c2 = st.columns(2)
        c1.metric(txt["total_words"], f"{total_word_count:,}")
        c2.metric(txt["est_time"], f"{est_hours:.1f} hrs", f"{est_hours/8:.1f} days")

        # 2. วิเคราะห์คำศัพท์
        filtered_words = [w for w in all_words_raw if w not in STOPWORDS and len(w) > 1]
        word_counts = Counter(filtered_words)
        top_words_dict = dict(word_counts.most_common(50)) # เก็บ 50 คำแรกไว้คิดคะแนนสรุป
        
        # 3. แสดงบทสรุป (Statistical Summary)
        st.subheader(txt["summary_title"])
        with st.expander("Show/Hide Summary", expanded=True):
            summary = statistical_summary(full_text, top_words_dict)
            st.write(f"_{summary}_")

        st.markdown("---")

        # 4. สร้างตาราง Glossary
        top_30 = word_counts.most_common(30)
        df = pd.DataFrame(top_30, columns=[txt["col_word"], txt["col_freq"]])
        
        with st.spinner("กำลังแปลคำศัพท์..."):
            translator = GoogleTranslator(source='en', target='th' if lang_key=="TH" else 'en')
            df[txt["col_trans"]] = [translator.translate(w) for w in df[txt["col_word"]]]
            
            # ดึง Context และ Collocates
            sentences = re.split(r'(?<=[.!?])\s+', full_text.replace('\n', ' '))
            df[txt["col_context"]] = [next((s.strip() for s in sentences if re.search(rf'\b{w}\b', s, re.I)), "-") for w in df[txt["col_word"]]]
            
            def get_col(target, all_w):
                near = []
                for i, v in enumerate(all_w):
                    if v == target: near.extend(all_w[max(0, i-2):i] + all_w[i+1:i+3])
                res = [c[0] for c in Counter([n for n in near if n != target and n not in STOPWORDS]).most_common(2)]
                return ", ".join(res) if res else "-"
            df[txt["col_collocate"]] = [get_col(w, all_words_raw) for w in df[txt["col_word"]]]

        # แสดงกราฟและตาราง
        st.subheader(txt["chart_title"])
        st.bar_chart(df.set_index(txt["col_word"])[txt["col_freq"]])
        
        st.subheader(txt["table_title"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ปุ่มดาวน์โหลด
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button(txt["btn_download"], buffer.getvalue(), "glossary.xlsx")
