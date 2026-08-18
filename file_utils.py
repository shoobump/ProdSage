import pypdf
import docx
import io

def extract_text_from_file(uploaded_file):
    filename = uploaded_file.name.lower()

    if filename.endswith('.txt'):
        return uploaded_file.read().decode('utf-8')

    elif filename.endswith('.pdf'):
        reader = pypdf.PdfReader(uploaded_file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        return text

    elif filename.endswith('.docx'):
        doc = docx.Document(uploaded_file)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return text

    else:
        return None