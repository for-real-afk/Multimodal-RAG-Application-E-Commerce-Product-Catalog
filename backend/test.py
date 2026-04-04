from google import genai
import os
import base64
import requests
from typing import List, Optional, Dict, Any
from google import genai
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

for m in client.models.list():
    print(m.name, getattr(m, "supported_generation_methods", []))