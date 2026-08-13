import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("API KEY:")
print(os.getenv("OPENAI_API_KEY"))

print("\nMODEL:")
print(os.getenv("OPENAI_MODEL"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    messages=[
        {
            "role": "user",
            "content": "Hei"
        }
    ]
)

print(response.choices[0].message.content)