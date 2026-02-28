import google.generativeai as genai
import traceback
import sys

try:
    m = genai.GenerativeModel('gemini-2.5-flash', tools='google_search_retrieval')
    print("Model created successfully with tools='google_search_retrieval'")
except Exception as e:
    print(f"Error creating model: {repr(e)}")

try:
    m = genai.GenerativeModel('gemini-2.5-flash', tools='google_search')
    print("Model created successfully with tools='google_search'")
except Exception as e:
    print(f"Error creating model: {repr(e)}")
