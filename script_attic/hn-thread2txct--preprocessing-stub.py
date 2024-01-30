import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

def chunk_text(text, chunk_size=14000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def send_to_chatgpt(instruction, topic, chunks):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    url = "https://api.openai.com/v1/chat/completions"
    instruction = "\n".join([topic,instruction])
    for chunk in chunks:
        data = {
            "model": "gpt-3.5-turbo-16k",
            "messages": [
                {
                    "role": "assistant",
                    "content": instruction
                },
                {
                    "role": "user",
                    "content": chunk
                }
            ],
            "temperature": 0.1,
            "top_p": 1,
            "n": 1,
            "stream": False,
            "max_tokens": 2500,
            "presence_penalty": 0,
            "frequency_penalty": 0
        }
        data = json.dumps(data)
        response = requests.post(url, headers=headers, data=data)
        response_json = response.json()

        if response.status_code == 200:
            print(response_json['choices'][0]['message']['content'])
        else:
            print(f"Error: {response_json['error']['message']}")

if __name__ == "__main__":
    instruction = """
You will be provided with meeting notes about this topic.  
Summarize the arguments, keyword-style, max 20 keywords. 
Provide a table:

- Participant/User name | Argument|  Argument comment/objections/questions (keyword-style)

Some info about the input format: ContributionTopics are separated by 4 or more empty lines.
User names can be found in lines containing a substring  matching  the regex '^\s*\[\d+\]\w+'  . 
If no username is obvious, write (unknown). 
If URLs are mentioned , include them a column. URLs match '- [\d+\]https://.+$'  .
"""    
    text = """
   I don't think people should be too concerned with black bears in the
   Sierras. I had a lot of run ins, they just saunter or run away.
   Especially when you'll be surrounded by 100 other people on that rock.
   Mountain lions, on the other hand...
"""
    topic = "Open Challenges in LLM Research"
    topic = ": ".join(["The topic was", topic])
    chunks = chunk_text(text)
    send_to_chatgpt(instruction, topic, chunks)
   