import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

# Modern Standalone LangChain Imports (No Deprecation Warnings)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables (.env)
load_dotenv()

# Page configuration
st.set_page_config(page_title="Autonomous PDF RAG Bot", page_icon="🧠", layout="wide")
st.title("🧠 Autonomous PDF Intelligence Agent")
st.caption("Upload a document, and let the reasoning layer analyze and extract data cleanly.")

# Initialize embedding model and LLM once
@st.cache_resource
def load_core_models():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    llm = ChatGroq(model="llama-3.3-70b-versatile")
    return embeddings, llm

embeddings_model, llm = load_core_models()

# Chat Prompt Template Setup
template = ChatPromptTemplate.from_messages([
    ("system", "You are an helpful AI assistant. Use only the provided context to answer the user's question. If the context does not contain the answer, say you don't know."),
    ("human", "Context: {context}\n\nQuestion: {question}")
])

# Initialize Chat History Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for MULTIPLE PDF Ingestion
with st.sidebar:
    st.header("📥 Document Ingestion")
    # 1. ALLOW MULTIPLE FILES BY SETTING accept_multiple_files=True
    uploaded_files = st.file_uploader("Upload your source PDFs", type=["pdf"], accept_multiple_files=True)
    
    # Process PDFs if the list is not empty
    if uploaded_files: # This is now a list of files
        with st.spinner(f"Processing {len(uploaded_files)} document(s)..."):
            all_chunks = []
            
            # 2. Loop through every single file the user uploaded
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                try:
                    loader = PyPDFLoader(tmp_file_path)
                    docs = loader.load()
                    
                    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    chunks = splitter.split_documents(docs)
                    
                    # Add these chunks to our master list
                    all_chunks.extend(chunks)
                finally:
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
            
            # 3. Create a single Vector Store containing data from ALL files
            vectorstore = Chroma.from_documents(
                documents=all_chunks,
                embedding=embeddings_model
            )
            
            # 4. Expose the MMR Retriever
            st.session_state.retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "fetch_k": 15, "lambda_mult": 0.5}
            )
            st.success(f"Successfully indexed {len(uploaded_files)} files!")
    else:
        st.session_state.retriever = None
        st.info("Please upload one or more PDF files to begin.")
# Main Chat Interface Workspace
if st.session_state.retriever is None:
    st.warning("⚠️ No database context found. Please drop a PDF document into the sidebar upload panel to start asking questions.")
else:
    # Render historical conversation elements on screen refresh
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Wait for natural chat input from user
    if query := st.chat_input("Ask your document anything..."):
        # Display human question in chat window immediately
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        # Process retrieval and execution loops inside an AI bubble block
        with st.chat_message("assistant"):
            with st.spinner("Analyzing context blocks..."):
                # 1. Fetch relevant vector data using MMR
                docs = st.session_state.retriever.invoke(query)
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # 2. Generate Prompt and pass to Groq LLM
                final_prompt = template.invoke({"context": context, "question": query})
                response = llm.invoke(final_prompt)
                
                # 3. Print answer out clean
                st.markdown(response.content)
                
        # Append AI payload responses into context memory arrays
        st.session_state.messages.append({"role": "assistant", "content": response.content})