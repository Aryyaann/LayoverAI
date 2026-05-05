import os
import pathlib
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

BASE_DIR = pathlib.Path(__file__).parent.parent
CHROMA_DIR = str(BASE_DIR / "chroma_db")
DOCS_DIR = str(BASE_DIR / "docs")

def load_and_index_documents():
    """
    Loads all PDFs from the docs/ folder, splits them into chunks,
    creates embeddings and stores them in ChromaDB.
    """
    documents = []

    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(DOCS_DIR, filename)
            print(f"Loading {filename}...")
            loader = PyPDFLoader(filepath)
            pages = loader.load()
            for page in pages:
                page.metadata["airport"] = filename.replace(".pdf", "")
            documents.extend(pages)

    if not documents:
        print("No PDFs found in docs/ folder.")
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(documents)} pages.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    vectorstore.persist()

    print(f"Indexed {len(chunks)} chunks into ChromaDB.")
    return vectorstore


def get_vectorstore():
    """
    Loads existing ChromaDB vectorstore if it exists,
    otherwise creates it from scratch.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        print("Loading existing ChromaDB...")
        return Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
    else:
        print("No existing ChromaDB found. Creating from documents...")
        return load_and_index_documents()


def query_airport_procedures(vectorstore, airport: str, query: str, k: int = 4) -> str:
    """
    Queries the vectorstore for relevant airport procedures.
    Filters by airport name if possible.
    """
    if vectorstore is None:
        return "No airport documentation available."

    try:
        results = vectorstore.similarity_search(
            query=f"{airport} {query}",
            k=k
        )

        if not results:
            return f"No specific procedures found for {airport}."

        context = f"Airport procedures for {airport}:\n\n"
        for i, doc in enumerate(results, 1):
            context += f"[{i}] {doc.page_content}\n\n"

        return context

    except Exception as e:
        return f"Error querying airport procedures: {str(e)}"