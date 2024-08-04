import requests

def callapi(question):
    url = "https://1073-105-27-226-165.ngrok-free.app/ask"  

    payload = {
        "question": question
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        ans=data.get("answer")
        #print("Answer:", data.get("answer"))
        #print("Sources:", data.get("sources"))
    else:
        print("Error:", response.status_code, response.text)
    return ans

question="who's the vice chancellor of dmu"
ai_answer=callapi(question)
print(ai_answer)