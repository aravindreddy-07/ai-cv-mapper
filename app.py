import streamlit as st
import re
from docx import Document
from docxtpl import DocxTemplate
import PyPDF2
import io

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

def parse_cv_with_rules(cv_text):
    """Use rule-based parsing to extract CV data (FREE - no API needed)"""
    data = {
        'name': '',
        'email': '',
        'phone': '',
        'address': '',
        'summary': '',
        'education': [],
        'experience': [],
        'skills': [],
        'certifications': [],
        'projects': []
    }
    
    lines = cv_text.split('\n')
    
    # Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    for line in lines:
        email_match = re.search(email_pattern, line)
        if email_match:
            data['email'] = email_match.group()
            break
    
    # Extract phone
    phone_patterns = [
        r'\+?\d{1,3}[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
        r'\d{10}',
        r'\(\d{3}\)\s*\d{3}-\d{4}'
    ]
    for line in lines:
        for pattern in phone_patterns:
            phone_match = re.search(pattern, line)
            if phone_match:
                data['phone'] = phone_match.group()
                break
        if data['phone']:
            break
    
    # Extract name (usually first non-empty line or line before email/phone)
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        if line and len(line.split()) <= 4 and not re.search(email_pattern, line) and len(line) > 3:
            if not any(char.isdigit() for char in line):
                data['name'] = line
                break
    
    # Extract sections
    current_section = None
    section_keywords = {
        'education': ['education', 'academic', 'qualification', 'degree'],
        'experience': ['experience', 'employment', 'work history', 'professional'],
        'skills': ['skills', 'technical skills', 'competencies'],
        'certifications': ['certification', 'certificates', 'licenses'],
        'projects': ['projects', 'portfolio'],
        'summary': ['summary', 'objective', 'profile', 'about']
    }
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if line is a section header
        for section, keywords in section_keywords.items():
            if any(keyword in line_lower for keyword in keywords) and len(line.split()) <= 4:
                current_section = section
                break
        else:
            # Add content to current section
            if current_section and line.strip():
                if current_section == 'summary':
                    data['summary'] += line.strip() + ' '
                elif isinstance(data[current_section], list):
                    if line.strip() and len(line.strip()) > 10:
                        data[current_section].append(line.strip())
    
    # Clean up summary
    data['summary'] = data['summary'].strip()
    
    return data

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
    st.title("🤖 AI CV Mapper Agent (FREE Version)")
    st.markdown("**Automatically extract content from your old CV and populate a new template**")
    st.info("✨ This version uses smart rule-based parsing - NO API KEY NEEDED!")
    
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
            
            # Parse with rules
            try:
                parsed_data = parse_cv_with_rules(cv_text)
                st.info("✓ Parsed CV with intelligent rules")
                
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
