import streamlit as st
from interview import start_interview, continue_interview
from file_utils import extract_text_from_file

st.set_page_config(page_title='PM Interview Practice', page_icon='🎤')
st.title('PM Interview Practice Bot')

if 'stage' not in st.session_state:
    st.session_state.stage = 'intake'

def get_field_input(label, key_prefix, height=120):
    mode = st.radio(
        f'{label} — input method',
        ['Paste text', 'Upload file'],
        key=f'{key_prefix}_mode',
        horizontal=True
    )

    if mode == 'Paste text':
        return st.text_area(label, height=height, key=f'{key_prefix}_text')
    else:
        uploaded = st.file_uploader(
            f'Upload {label} (.txt, .pdf, .docx)',
            type=['txt', 'pdf', 'docx'],
            key=f'{key_prefix}_file'
        )
        if uploaded:
            extracted = extract_text_from_file(uploaded)
            if extracted:
                st.success(f'Extracted {len(extracted)} characters from {uploaded.name}')
                with st.expander('Preview extracted text'):
                    st.text(extracted[:1000])
                return extracted
            else:
                st.error('Could not read that file type.')
                return None
        return None

if st.session_state.stage == 'intake':
    st.subheader('Set up your mock interview')

    st.markdown('**Company profile**')
    company_profile = get_field_input('Company profile', 'company', height=100)

    st.markdown('**Job description**')
    job_description = get_field_input('Job description', 'jd', height=150)

    st.markdown('**Your CV**')
    cv_text = get_field_input('CV', 'cv', height=150)

    if st.button('Start interview', type='primary'):
        if company_profile and job_description and cv_text:
            with st.spinner('Finding your interviewer...'):
                guest, history, first_message = start_interview(company_profile, job_description, cv_text)
            st.session_state.guest = guest
            st.session_state.history = history
            st.session_state.stage = 'interview'
            st.rerun()
        else:
            st.warning('Please provide all three: company profile, job description, and CV.')

elif st.session_state.stage == 'interview':
    st.caption(f'Interviewer: {st.session_state.guest}')

    for msg in st.session_state.history:
        if msg['role'] == 'assistant':
            with st.chat_message('assistant'):
                st.write(msg['content'])
        elif msg['role'] == 'user':
            with st.chat_message('user'):
                st.write(msg['content'])

    user_input = st.chat_input('Your answer...')

    if user_input:
        with st.chat_message('user'):
            st.write(user_input)
        with st.spinner('Thinking...'):
            history, reply = continue_interview(st.session_state.history, user_input)
        st.session_state.history = history
        with st.chat_message('assistant'):
            st.write(reply)

    if st.button('End interview & start new session'):
        st.session_state.stage = 'intake'
        st.session_state.pop('history', None)
        st.session_state.pop('guest', None)
        st.rerun()