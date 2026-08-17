Streamlit Gemini Chat

A single-page Streamlit app that looks like ChatGPT: chat sidebar, persistent message history (local JSON), and a modern chat input at the bottom. Integrates Google Gemini (Generative API) when available and configured.

Features
- Sidebar with chat list, new/rename/delete chats
- Persistent message history saved to chats.json
- Assistant responses rendered as Markdown with fenced code blocks for syntax highlighting
- Uses Google Generative AI (Gemini) if google-generative-ai is installed and GOOGLE_API_KEY is set

Security note
Do not commit your GOOGLE_API_KEY or service account JSON to a public repository. Use environment variables or your host's secrets manager.

Installation
1. Clone or copy files to a folder, e.g. C:\Users\ccuk\streamlit_chatgpt_clone
2. (Optional) Create and activate a Python virtual environment

3. Install dependencies:

    pip install -r requirements.txt

4. Set the Google API key (one of):

- Environment variable (recommended):

    setx GOOGLE_API_KEY "YOUR_KEY"
    (Restart your terminal / IDE to pick up the variable)

- Or use Streamlit secrets when deploying on Streamlit Cloud: in the app's settings, set secret key `google_api_key`.

5. (Optional) choose a model via GEMINI_MODEL env var. Default: models/text-bison-001

Running locally

    streamlit run app.py

Open the URL shown (usually http://localhost:8501).

Hosting

- Streamlit Community Cloud: push this repo to GitHub, create a new app in Streamlit Cloud, set the `google_api_key` secret in the app settings and deploy.
- Other hosts (Heroku, AWS, GCP App Engine): set the environment variable `GOOGLE_API_KEY` and run `streamlit run app.py` as the web command.

How it uses Gemini

The app expects the `google-generative-ai` client (package name `google-generative-ai`) and an API key in `GOOGLE_API_KEY`. The code calls `genai.generate_text(model=model, prompt=...)`. Model name is configurable by `GEMINI_MODEL` env var.

If the client or key is missing, the app provides helpful messages and falls back to showing the user's input as a code block.

Troubleshooting
- If you see an API error, check that the key is correct and has access to the Generative API.
- If you want richer code formatting, install `pygments` or use the Streamlit secrets for advanced rendering.

License
MIT
