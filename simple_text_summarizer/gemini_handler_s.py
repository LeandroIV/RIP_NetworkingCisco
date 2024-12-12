import google.generativeai as genai

# Replace with your actual Gemini API key
API_KEY = 'API_KEY_HERE'

class GeminiHandler:
    def __init__(self, api_key):
        # Configure Gemini AI with the provided API key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def summarize_text(self, text):
        prompt = f"Please summarize the following text: {text}"
        response = self.model.generate_content(prompt)
        return response.text
