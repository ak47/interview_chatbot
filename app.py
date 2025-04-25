from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from typing import List

st.set_page_config(page_title="Stremlit chat", page_icon="💬")
st.title('Chattybot')

for var, default in {'setup_complete': False,
                     'user_message_count': 0,
                     'feedback_shown': False,
                     'messages': [],
                     'chat_complete': False}.items():
    if var not in st.session_state:
        st.session_state[var] = default


def complete_setup() -> None:
    st.session_state.setup_complete = True


def show_feedback() -> None:
    st.session_state.feedback_shown = True


if not st.session_state.setup_complete:
    st.subheader('personal info', divider='rainbow')

    for var in ['name', 'experience', 'skills']:
        if var not in st.session_state:
            st.session_state[var] = ''

    st.session_state['name'] = st.text_input(label='Name',
                                             max_chars=40,
                                             placeholder='enter your name')
    st.session_state['experience'] = st.text_area(label='Experience',
                                                  value='',
                                                  height=None,
                                                  max_chars=200,
                                                  placeholder='Describe your experience')
    st.session_state['skills'] = st.text_area(label='Skills',
                                              value='',
                                              height=None,
                                              max_chars=200,
                                              placeholder='List your skills')

    st.subheader('company and position', divider='rainbow')

    for var, default in {'level': 'junior', 'position': 'data engineer', 'company': 'disney'}.items():
        if var not in st.session_state:
            st.session_state[var] = default

    col1, col2 = st.columns(2)
    with col1:
        st.session_state['level'] = st.radio(
            'Choose level',
            key='visibility',
            options=['junior', 'mid', 'senior']
        )

    with col2:
        st.session_state['position'] = st.selectbox(
            'choose position',
            ('data scientist', 'data engineer', 'ML engineer', 'BI analyst', 'financial analyst')
        )

    st.session_state['company'] = st.selectbox(
        'choose a company',
        ('amazon', 'meeta', 'udemy', 'disney', 'google', 'openai')
    )

    if st.button('start interview', on_click=complete_setup):
        st.write('setup complete. starting Interview...')

if st.session_state.setup_complete \
        and not st.session_state.feedback_shown \
        and not st.session_state.chat_complete:

    st.info(
        """
        Start by introducing yourself
        """,
        icon='🤙🏼'
    )
    client = OpenAI(api_key=st.secrets['OPEN_AI_KEY'])

    if "openai_model" not in st.session_state:
        st.session_state['openai_model'] = 'gpt-4o'

    if not st.session_state.messages:
        system_context = f'''
        You are an HR executive that interviews an interviewee called {st.session_state['name']} with experience 
            {st.session_state['experience']} and skills {st.session_state['skills']}.
        You should interview them for the position 
            {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}.
        You should respond with the tone of a valley boy.
        '''
        st.session_state.messages = [{'role': 'system', 'content': system_context}]

    for message in st.session_state.messages:
        if message['role'] != 'system':
            with st.chat_message(message['role']):
                st.markdown(message['content'])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input('your answer:', max_chars=1000):
            st.session_state.messages.append({'role': 'user', 'content': prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message('assistant'):
                    user_messages: List[ChatCompletionUserMessageParam] = []
                    for m in st.session_state.messages:
                        user_messages.append({
                            "role": m['role'],
                            "content": m['content']
                        })
                    stream = client.chat.completions.create(
                        model=st.session_state['openai_model'],
                        messages=user_messages,
                        stream=True
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({'role': 'assistant', 'content': response})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button('Get Feedback', on_click=show_feedback):
        st.write('Fetching feedback bro...')

if st.session_state.feedback_shown:
    st.subheader('Feedback')

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets['OPEN_AI_KEY'])

    feedback_completion = feedback_client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': '''you are a helpful tool that provides feedback on an interview performance.
            Before the feedback give a score of 1 to 10.
            Follow this format:
            Overall score: // your score
            Feedback: // here you put your feedback
            Give only the feedback, do not ask any additional questions.
            '''},
            {'role': 'user', 'content': f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in conversation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button('restart interview', type='primary'):
        streamlit_js_eval(js_expression="parent.window.location.reload()")