# Contributing

## Setup

```bash
git clone https://github.com/kairav7220/pdf-rag-chat.git
cd pdf-rag-chat
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Development

- Fork the repo, create a feature branch.
- Test with `streamlit run app.py` and upload a test PDF.
- Ensure `chroma_db/`, `chroma-db/`, `vector store/` are in `.gitignore`.
- No hardcoded secrets — always use `.env`.

## PR Guidelines

- One feature/fix per PR.
- Include a test PDF in the PR description if adding document format support.
- Update `requirements.txt` if adding dependencies.
