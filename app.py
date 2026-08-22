import random
import concurrent.futures
import streamlit as st
from interview import start_interview, continue_interview, generate_debrief, start_interview_with_guest, generate_quick_feedback
from persona import get_persona_context, get_top_guests
from file_utils import extract_text_from_file
from learn import search_topics, search_experts, get_expert_reading, get_all_topics, get_all_guest_names

st.set_page_config(page_title='PM Sage', page_icon='🧭', layout='wide')

if 'mode' not in st.session_state:
    st.session_state.mode = None

CURATED_TOPICS = ['Product Strategy', 'Growth & Metrics', 'UX & Design', 'Leadership & Management', 'Go-to-Market']
CURATED_EXPERTS = ['Shreyas Doshi', 'Julie Zhuo', 'Marty Cagan', 'Teresa Torres', 'Melissa Perri']


def get_field_input(label, key_prefix, height=120):
    mode = st.radio(
        'Input method',
        ['Paste text', 'Upload file'],
        key=f'{key_prefix}_mode',
        horizontal=True,
        label_visibility='collapsed'
    )

    if mode == 'Paste text':
        return st.text_area(label, height=height, key=f'{key_prefix}_text', label_visibility='collapsed', placeholder=label)
    else:
        uploaded = st.file_uploader(
            f'Upload {label} (.txt, .pdf, .docx)',
            type=['txt', 'pdf', 'docx'],
            key=f'{key_prefix}_file',
            label_visibility='collapsed'
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


# ─────────────────────────── HOME SCREEN ───────────────────────────

if st.session_state.mode is None:
    st.title('🧭 PM Sage')
    st.markdown('*Learn from, interview with, or talk to real product leaders — grounded in real podcast conversations.*')
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('### 📚 Learn from Sage')
        st.caption('Browse concepts and insights from product experts, by topic or by person.')
        if st.button('Learn from Sage', use_container_width=True):
            st.session_state.mode = 'learn'
            st.session_state.learn_stage = 'home'
            st.rerun()

    with col2:
        st.markdown('### 🎤 Interview with Sage')
        st.caption("Practice a mock interview grounded in a real expert's style.")
        if st.button('Interview with Sage', use_container_width=True):
            st.session_state.mode = 'interview'
            st.session_state.stage = 'intake'
            st.rerun()

    with col3:
        st.markdown('### 💬 Talk to Sage')
        st.caption('Coming soon — chat freely with an expert of your choice.')
        st.button('Talk to Sage', use_container_width=True, disabled=True)


# ─────────────────────────── INTERVIEW MODE ───────────────────────────

elif st.session_state.mode == 'interview':

    if st.session_state.stage == 'intake':
        if st.button('← Back to home'):
            st.session_state.mode = None
            st.rerun()

        st.title('🎤 Interview with Sage')
        st.markdown(
            '*Practice PM interviews with real expert voices, drawn from '
            'hundreds of hours of product leadership conversations.*'
        )
        st.divider()

        st.markdown('#### Company profile')
        company_profile = get_field_input('Company profile', 'company', height=100)

        st.markdown('#### Job description')
        job_description = get_field_input('Job description', 'jd', height=150)

        st.markdown('#### Your CV')
        cv_text = get_field_input('CV', 'cv', height=150)

        st.divider()

        if st.button('Start interview', type='primary', use_container_width=True):
            if company_profile and job_description and cv_text:
                with st.spinner('Finding your interviewer...'):
                    guest, history, first_message, sample_chunks = start_interview(company_profile, job_description, cv_text)
                    shortlist = get_top_guests(company_profile, job_description, n=4)

                st.session_state.guest = guest
                st.session_state.history = history
                st.session_state.sample_chunks = sample_chunks
                st.session_state.guest_shortlist = shortlist
                st.session_state.saved_company_profile = company_profile
                st.session_state.saved_job_description = job_description
                st.session_state.saved_cv_text = cv_text
                st.session_state.feedback_log = []
                st.session_state.stage = 'interview'
                st.rerun()
            else:
                st.warning('Please provide all three: company profile, job description, and CV.')

    elif st.session_state.stage == 'interview':
        left_col, center_col, right_col = st.columns([1, 2, 1])

        with left_col:
            st.markdown('#### Context')
            with st.expander('Company profile'):
                st.caption(st.session_state.saved_company_profile[:600])
            with st.expander('Job description'):
                st.caption(st.session_state.saved_job_description[:600])
            with st.expander('CV'):
                st.caption(st.session_state.saved_cv_text[:600])

            st.divider()
            st.markdown('#### Interviewer')
            st.write(f"**{st.session_state.guest}**")

            alternatives = [g for g in st.session_state.guest_shortlist if g != st.session_state.guest]
            if alternatives:
                chosen = st.selectbox('Switch interviewer', ['Keep current'] + alternatives, key='switch_select')
                if chosen != 'Keep current' and st.button('Confirm switch', use_container_width=True):
                    with st.spinner(f'Switching to {chosen}...'):
                        guest, history, first_message, sample_chunks = start_interview_with_guest(
                            chosen,
                            st.session_state.saved_company_profile,
                            st.session_state.saved_job_description,
                            st.session_state.saved_cv_text
                        )
                    st.session_state.guest = guest
                    st.session_state.history = history
                    st.session_state.sample_chunks = sample_chunks
                    st.session_state.feedback_log = []
                    st.rerun()

        with center_col:
            st.markdown('#### Interview')

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
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        reply_future = executor.submit(continue_interview, st.session_state.history, user_input)
                        feedback_future = executor.submit(generate_quick_feedback, st.session_state.guest, user_input, st.session_state.sample_chunks)

                        history, reply = reply_future.result()
                        feedback = feedback_future.result()

                st.session_state.history = history
                st.session_state.feedback_log.append(feedback)

                with st.chat_message('assistant'):
                    st.write(reply)

            st.divider()
            if st.button('End interview & see improvement areas', use_container_width=True):
                st.session_state.stage = 'debrief'
                st.rerun()

        with right_col:
            st.markdown('#### Live Feedback')
            if not st.session_state.feedback_log:
                st.caption('Feedback on each answer will appear here as you go.')
            else:
                for fb in reversed(st.session_state.feedback_log):
                    st.info(fb)

    elif st.session_state.stage == 'debrief':
        st.title('🎤 Interview with Sage')
        st.caption(f'Interviewer: **{st.session_state.guest}**')
        st.subheader('Improvement Areas')

        if 'debrief_text' not in st.session_state:
            with st.spinner(f'{st.session_state.guest} is putting together feedback...'):
                debrief_text = generate_debrief(
                    st.session_state.guest,
                    st.session_state.history,
                    st.session_state.sample_chunks
                )
            st.session_state.debrief_text = debrief_text

        st.markdown(st.session_state.debrief_text)

        st.divider()
        if st.button('Start a new interview', type='primary', use_container_width=True):
            st.session_state.stage = 'intake'
            for key in ['history', 'guest', 'sample_chunks', 'debrief_text', 'guest_shortlist',
                        'saved_company_profile', 'saved_job_description', 'saved_cv_text', 'feedback_log']:
                st.session_state.pop(key, None)
            st.rerun()

        if st.button('← Back to home', use_container_width=True):
            st.session_state.mode = None
            st.session_state.stage = 'intake'
            for key in ['history', 'guest', 'sample_chunks', 'debrief_text', 'guest_shortlist',
                        'saved_company_profile', 'saved_job_description', 'saved_cv_text', 'feedback_log']:
                st.session_state.pop(key, None)
            st.rerun()


# ─────────────────────────── LEARN MODE ───────────────────────────

elif st.session_state.mode == 'learn':

    if st.session_state.learn_stage == 'home':
        if st.button('← Back to home'):
            st.session_state.mode = None
            st.session_state.pop('learn_home_topics', None)
            st.session_state.pop('learn_home_experts', None)
            st.rerun()

        st.title('📚 Learn from Sage')
        st.markdown('*Browse product insights by topic or by expert.*')
        st.divider()

        # Stable per-visit picks: 5 curated + 1 random, generated once and stored
        # so button clicks don't get scrambled by a fresh random draw mid-click.
        if 'learn_home_topics' not in st.session_state:
            all_topics = get_all_topics()
            remaining = [t for t in all_topics if t not in CURATED_TOPICS]
            random_topic = random.choice(remaining) if remaining else CURATED_TOPICS[0]
            st.session_state.learn_home_topics = CURATED_TOPICS + [random_topic]

        if 'learn_home_experts' not in st.session_state:
            all_experts = get_all_guest_names()
            remaining_experts = [e for e in all_experts if e not in CURATED_EXPERTS]
            random_expert = random.choice(remaining_experts) if remaining_experts else CURATED_EXPERTS[0]
            st.session_state.learn_home_experts = CURATED_EXPERTS + [random_expert]

        categories = st.session_state.learn_home_topics
        example_experts = st.session_state.learn_home_experts

        # Manual tab toggle (instead of st.tabs) so "back" navigation can
        # programmatically land on the right one.
        if 'learn_home_active_tab' not in st.session_state:
            st.session_state.learn_home_active_tab = 'Search by topic'

        st.radio(
            'View',
            ['Search by topic', 'Search by expert'],
            key='learn_home_active_tab',
            horizontal=True,
            label_visibility='collapsed'
        )
        active_tab = st.session_state.learn_home_active_tab
        st.divider()

        if active_tab == 'Search by topic':
            st.caption('Quick picks')
            cat_cols = st.columns(3)
            for i, cat in enumerate(categories):
                if cat_cols[i % 3].button(cat, use_container_width=True, key=f'cat_{i}'):
                    st.session_state.learn_topic_query = cat
                    st.session_state.learn_stage = 'topic_results'
                    st.rerun()

            st.write('')
            topic_query = st.text_input('Or search any topic (type and press enter)', placeholder='e.g. pricing strategy, retention, PM interviews', key='topic_search_input')

            if topic_query and len(topic_query) >= 3:
                all_topics = get_all_topics()
                suggestions = [t for t in all_topics if topic_query.lower() in t.lower()][:5]
                if suggestions:
                    st.caption('Suggestions:')
                    sugg_cols = st.columns(len(suggestions))
                    for i, s in enumerate(suggestions):
                        if sugg_cols[i].button(s, key=f'topic_sugg_{i}'):
                            st.session_state.learn_topic_query = s
                            st.session_state.learn_stage = 'topic_results'
                            st.rerun()

            if st.button('Search', type='primary') and topic_query:
                st.session_state.learn_topic_query = topic_query
                st.session_state.learn_stage = 'topic_results'
                st.rerun()

        else:  # Search by expert
            st.caption('Example experts')
            exp_cols = st.columns(3)
            for i, exp in enumerate(example_experts):
                if exp_cols[i % 3].button(exp, use_container_width=True, key=f'exp_{i}'):
                    st.session_state.learn_selected_expert = exp
                    st.session_state.learn_reading_origin = 'home'
                    st.session_state.learn_stage = 'expert_reading'
                    st.rerun()

            st.write('')
            expert_query = st.text_input('Search for an expert by topic/expertise (type and press enter)', placeholder='e.g. growth PM, enterprise sales, design leadership', key='expert_search_input')

            if expert_query and len(expert_query) >= 3:
                live_matches = search_experts(expert_query, n=5)
                if live_matches:
                    st.caption('Matching experts:')
                    sugg_cols = st.columns(len(live_matches))
                    for i, m in enumerate(live_matches):
                        if sugg_cols[i].button(m['guest'], key=f'expert_sugg_{i}'):
                            st.session_state.learn_selected_expert = m['guest']
                            st.session_state.learn_reading_origin = 'home'
                            st.session_state.learn_stage = 'expert_reading'
                            st.rerun()

            if st.button('Search experts', type='primary') and expert_query:
                st.session_state.learn_expert_query = expert_query
                st.session_state.learn_stage = 'expert_results'
                st.rerun()

    elif st.session_state.learn_stage == 'topic_results':
        query = st.session_state.learn_topic_query

        if st.button('← New topic search'):
            st.session_state.learn_home_active_tab = 'Search by topic'
            st.session_state.learn_stage = 'home'
            st.rerun()

        st.title('📚 Learn from Sage')
        st.markdown(f'#### Concepts on: *{query}*')
        st.divider()

        with st.spinner('Finding concepts across experts...'):
            results = search_topics(query, max_results=8)

        for r in results:
            with st.container(border=True):
                st.markdown(f"**{r['guest']}** · _{r['topic']}_")
                st.write(r['summary'])

    elif st.session_state.learn_stage == 'expert_results':
        query = st.session_state.learn_expert_query

        if st.button('← New search'):
            st.session_state.learn_home_active_tab = 'Search by expert'
            st.session_state.learn_stage = 'home'
            st.rerun()

        st.title('📚 Learn from Sage')
        st.markdown(f'#### Experts matching: *{query}*')
        st.divider()

        with st.spinner('Finding matching experts...'):
            results = search_experts(query, n=8)

        for r in results:
            with st.container(border=True):
                st.markdown(f"**{r['guest']}**")
                st.write(r['summary'])
                if st.button(f"Read {r['guest']}'s concepts", key=f"read_{r['guest']}"):
                    st.session_state.learn_selected_expert = r['guest']
                    st.session_state.learn_reading_origin = 'search'
                    st.session_state.learn_stage = 'expert_reading'
                    st.rerun()

    elif st.session_state.learn_stage == 'expert_reading':
        guest = st.session_state.learn_selected_expert
        origin = st.session_state.get('learn_reading_origin', 'home')

        back_label = '← Back to search results' if origin == 'search' else '← Back to experts'
        if st.button(back_label):
            if origin == 'search':
                st.session_state.learn_stage = 'expert_results'
            else:
                st.session_state.learn_home_active_tab = 'Search by expert'
                st.session_state.learn_stage = 'home'
            st.rerun()

        st.title('📚 Learn from Sage')
        st.markdown(f'#### Reading: {guest}')
        st.divider()

        with st.spinner(f"Loading {guest}'s concepts..."):
            entries = get_expert_reading(guest)

        for entry in entries:
            with st.container(border=True):
                st.markdown(f"**{entry['topic']}**")
                st.write(entry['summary'])


# ─────────────────────────── FOOTER (shown on every screen) ───────────────────────────

st.divider()
st.caption("Concepts and interview personas in this tool are drawn from conversations on Lenny's Podcast, hosted by Lenny Rachitsky.")