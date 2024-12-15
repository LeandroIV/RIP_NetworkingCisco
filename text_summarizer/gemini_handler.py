import google.generativeai as genai

API_KEY = 'AIzaSyAOQ9GIThEhIz68y6xEfDHdWmuNNiYSdCQ'

class GeminiHandler:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def summarize_text(self, text):
        prompt = f"Please summarize the following text: {text}"
        response = self.model.generate_content(prompt)
        return response.text