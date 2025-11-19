import google.generativeai as genai
import os

# Replace with your actual key
API_KEY = "AIzaSyAlkt7lKVOojR55cXeXI__hwI82j1QOflY" 

genai.configure(api_key=API_KEY)

print("Available Models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)