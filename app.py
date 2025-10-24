import streamlit as st
import re
import json
from docx import Document
from docxtpl import DocxTemplate
import PyPDF2
import io
import anthropic
import os

st.set_page_config(page_title="AI CV Mapper", page_icon="📄", layout="wide")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file"""
    doc = Document(docx_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def parse_cv_with_ai(cv_text, api_key):
    """Use Claude AI to parse CV and extract structured data"""
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Extract the following information from this CV and return ONLY a valid JSON object with these exact keys:
    - name
    - email
    - phone
    - address
    - summary
    - education (as a list of strings)
    - experience (as a list of strings)
    - skills (as a list of strings)
    - certifications (as a list of strings)
    - projects (as a list of strings)

    CV Content:
    {cv_text}

    Return ONLY the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(response_text)

def fill_template(template_file, data):
    """Fill DOCX template with extracted data"""
    doc = DocxTemplate(template_file)
    
    # Convert lists to formatted strings
    context = {}
    for key, value in data.items():
        if isinstance(value, list):
            context[key] = "\n".join([f"• {item}" for item in value]) if value else "N/A"
        else:
            context[key] = value if value else "N/A"
    
    doc.render(context)
    
    # Save to bytes
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def main():
    st.title("🤖 AI CV Mapper Agent")
    st.markdown("**Automatically extract content from your old CV and populate a new template**")
    
    st.sidebar.header("⚙️ Configuration")
    api_key = st.sidebar.text_input("Anthropic API Key", type="password", help="Get your API key from console.anthropic.com")
    
    if not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to continue.")
        st.info("Don't have an API key? Get one at: https://console.anthropic.com/")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📤 Upload Old CV")
        old_cv = st.file_uploader("Upload your old CV (PDF or DOCX)", type=["pdf", "docx"], key="old")
        
        if old_cv:
            st.success(f"✅ Uploaded: {old_cv.name}")
    
    with col2:
        st.header("📥 Upload New Template")
        new_template = st.file_uploader("Upload new CV template (DOCX with placeholders)", type=["docx"], key="new")
        
        if new_template:
            st.success(f"✅ Uploaded: {new_template.name}")
            with st.expander("ℹ️ Template Instructions"):
                st.markdown("""
                Your DOCX template should contain placeholders like:
                - `{{name}}` - Full name
                - `{{email}}` - Email address
                - `{{phone}}` - Phone number
                - `{{address}}` - Address
                - `{{summary}}` - Professional summary
                - `{{education}}` - Education details
                - `{{experience}}` - Work experience
                - `{{skills}}` - Skills list
                - `{{certifications}}` - Certifications
                - `{{projects}}` - Projects
                """)
    
    if st.button("🚀 Generate New CV", type="primary", use_container_width=True):
        if not old_cv or not new_template:
            st.error("❌ Please upload both old CV and new template!")
            return
        
        with st.spinner("🔄 Processing your CV..."):
            # Extract text from old CV
            if old_cv.name.endswith('.pdf'):
                cv_text = extract_text_from_pdf(old_cv)
            else:
                cv_text = extract_text_from_docx(old_cv)
            
            st.info("✓ Extracted text from old CV")
            
            # Parse with AI
            try:
                parsed_data = parse_cv_with_ai(cv_text, api_key)
                st.info("✓ Parsed CV with AI")
                
                # Show extracted data
                with st.expander("📋 View Extracted Data"):
                    st.json(parsed_data)
                
                # Fill template
                filled_cv = fill_template(new_template, parsed_data)
                st.success("✅ Successfully generated new CV!")
                
                # Download button
                st.download_button(
                    label="⬇️ Download New CV",
                    data=filled_cv,
                    file_name="new_cv_filled.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
