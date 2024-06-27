import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import pandas as pd
import base64
from docx import Document
import io
from googletrans import Translator

# Set page configuration
st.set_page_config(page_title="Koustav's GenX Engine - CoTutor(supernova)", page_icon=":robot:", layout="wide")

# Load environment variables
load_dotenv()

# Initialize translator
translator = Translator()

# Supported languages and their codes
languages = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "Hindi": "hi",
    "German": "de"
}

# Custom CSS for styling
def add_custom_css():
    st.markdown("""
        <style>
        /* Space theme background */
        .stApp {
            background: url('https://wallpaperaccess.com/full/4379622.jpg');
            background-size: cover;
            color: #ffffff;
        }

        /* Header styling */
        header {
            background: rgba(20, 20, 20, 0.6);
            padding: 10px;
            border-radius: 10px;
            color: white;
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background: rgba(30, 30, 30, 0.4);
            color: #ffffff;
        }

        /* Input and buttons styling */
        .stTextInput > div > div > input {
            background: rgba(30, 30, 30, 0.6);
            color: #ffffff;
            border-radius: 10px;
        }

        .stButton > button {
            background: #0078D4;
            color: #ffffff;
            border: None;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.3s;
        }

        .stButton > button:hover {
            background: #005a9e;
        }

        /* Predefined questions select box */
        .stSelectbox > div > div {
            background: rgba(30, 30, 30, 0.4);
            color: #ffffff;
            border-radius: 10px;
        }

        /* Conversation history section */
        .stContainer {
            background: rgba(30, 30, 30, 0.4);
            border-radius: 10px;
            padding: 20px;
        }

        /* Download links */
        a.download-link {
            color: #ffcc00;
            text-decoration: None;
        }

        a.download-link:hover {
            text-decoration: underline;
        }

        /* General text color and headings */
        h1, h2, h3, h4, h5, h6 {
            color: white;
        }

        /* Custom subheading styles */
        .subheading {
            color: white;
        }
        
        /* Answer text color */
        .answer-text {
            color: black !important;
        }

        /* Info message color */
        .info-message {
            color: #ffcc00;
        }
        </style>
        """, unsafe_allow_html=True)

# Function to return the response with retry logic
def load_answer(question, conversation_history, pdf_text):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")
    
    # Include the conversation history and PDF context in the context
    context = pdf_text + "\n" + "\n".join(conversation_history) + f"\nUser: {question}\nAI:"
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            answer = llm.invoke(context)
            return answer.content
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.warning(f"Resource exhausted. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                st.error(f"An error occurred: {e}")
                break
    return "Failed to get a response after several attempts."

# Function to clear conversation history
def clear_history():
    st.session_state.conversation_history = []

# Function to download conversation history as text file
def download_history_text():
    history_str = "\n".join(st.session_state.conversation_history)
    b64 = base64.b64encode(history_str.encode()).decode()
    href = f'<a class="download-link" href="data:text/plain;base64,{b64}" download="conversation_history.txt">Download conversation history (TXT)</a>'
    st.markdown(href, unsafe_allow_html=True)

# Function to download conversation history as CSV file
def download_history_csv():
    history_df = pd.DataFrame(st.session_state.conversation_history, columns=["Conversation"])
    csv = history_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a class="download-link" href="data:file/csv;base64,{b64}" download="conversation_history.csv">Download conversation history (CSV)</a>'
    st.markdown(href, unsafe_allow_html=True)

# Function to extract text from DOCX file
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    content = ""
    for para in doc.paragraphs:
        content += para.text + "\n"
    return content

# Function to translate text
def translate_text(text, dest_lang):
    translation = translator.translate(text, dest=dest_lang)
    return translation.text

# Function to translate conversation history
def translate_conversation_history(conversation_history, dest_lang):
    translated_history = []
    for entry in conversation_history:
        translated_entry = translate_text(entry, dest_lang)
        translated_history.append(translated_entry)
    return translated_history

# Initialize the session state to store the conversation history and DOCX text
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'docx_text' not in st.session_state:
    docx_text = extract_text_from_docx(r"C:\Users\kousdutta\Desktop\Project_X\Files\Suheldev_Chapters.docx")
    st.session_state.docx_text = docx_text

if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

if 'response' not in st.session_state:
    st.session_state.response = ''

if 'feedback' not in st.session_state:
    st.session_state.feedback = []

if 'language' not in st.session_state:
    st.session_state.language = "English"

# Predefined questions
predefined_questions = [
    "Tell me about Suheldev.",
    "What is the main theme of Chapter 1?",
    "Describe the key events in the chapter.",
    "What is the historical context of the chapter?",
    "Who are the main characters introduced?"
]

# Add custom CSS for styling
add_custom_css()

# App UI starts here
st.header("CoTutor: GenX Engine Pilot")

# Language selection
selected_language = st.radio("Select Language", list(languages.keys()), index=0, key="language")
selected_lang_code = languages[selected_language]

# Sidebar for navigation
tab = st.sidebar.selectbox("Choose a section", ["Chat", "Conversation History"], key="section")

# Chat section
if tab == "Chat":
    # Function to get text input
    def get_text():
        input_text = st.text_input("You: ", key="input", value=st.session_state.user_input, on_change=reset_predefined_question)
        return input_text

    # Function to reset predefined question
    def reset_predefined_question():
        st.session_state.predefined_question = ""

    # Initialize predefined_question in session state
    if 'predefined_question' not in st.session_state:
        st.session_state.predefined_question = ""

    user_input = get_text()
    predefined_question = st.selectbox("Or select a predefined question:", [""] + predefined_questions, key="predefined_question")
    col1, col2 = st.columns([1, 1])
    with col1:
        submit = st.button('Generate')
    with col2:
        clear = st.button('Clear History')

    # If clear history button is clicked
    if clear:
        clear_history()

    # If generate button is clicked
    if submit and (user_input or predefined_question):
        # Use the predefined question if available
        question = predefined_question if predefined_question else user_input

        # Get the previous conversation history
        conversation_history = st.session_state.conversation_history

        # Generate response based on the current question and conversation history
        response = load_answer(question, conversation_history, st.session_state.docx_text)

        # Update the conversation history
        conversation_history.append(f"User: {question}")
        conversation_history.append(f"AI: {response}")

        # Save the updated conversation history, user input, and response in session state
        st.session_state.conversation_history = conversation_history
        st.session_state.user_input = user_input
        st.session_state.response = response

    # Display the latest response
    if st.session_state.response:
        st.subheader("Answer:")
        translated_response = translate_text(st.session_state.response, selected_lang_code)
        st.write(translated_response)

        # Add feedback section with star rating
        st.subheader("Rate the Response")
        rating = st.radio("How would you rate this response?", options=[1, 2, 3, 4, 5], format_func=lambda x: '⭐' * x, key='rating')
        feedback_text = st.text_area("Any additional feedback?", key='feedback_text')
        feedback_submit = st.button("Submit Feedback")

        if feedback_submit:
            feedback_entry = {
                'question': st.session_state.user_input or st.session_state.predefined_question,
                'response': st.session_state.response,
                'rating': rating,
                'feedback': feedback_text
            }
            st.session_state.feedback.append(feedback_entry)
            st.success("Thank you for your feedback!")

    # Display a message if there is no input
    if not user_input and not predefined_question and submit:
        st.error("Please enter a question or select a predefined question.")

# Conversation History section
elif tab == "Conversation History":
    st.subheader("Conversation History")
    conversation_history = st.session_state.conversation_history

    if conversation_history:
        translated_history = translate_conversation_history(conversation_history, selected_lang_code)
        for i in range(0, len(translated_history), 2):
            st.text(f"{translated_history[i]}")
            st.text(f"{translated_history[i+1]}")
        st.markdown("---")
        download_history_text()
        download_history_csv()
    else:
        st.info("No conversation history yet.")

# Apply custom styles to specific elements
st.markdown(
    """
    <style>
    .subheading {
        color: white !important;
    .download-link {
        color: #ffcc00 !important;
    }
    .info-message {
        color: #ffcc00 !important;
    }
    </style>
    """, unsafe_allow_html=True
)
