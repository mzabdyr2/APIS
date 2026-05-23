#imports
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def get_response(messages: list[dict], model: str='llama3.2') -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7, # kreatywność - im większa wartość tym model bardziej kreatywny i zaczyna halucynować
        top_p=0.9, # weź tylko te tokeny których skumulowane prawdopodobieństwo wynosi p - czyli np. z jakiejś puli słów bierzemy tylko te które mieszczą się w sumie prawodopodobieństw
        max_tokens = 1024, # długość odpowiedzi
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    test_messages = [
        {"role":"user", "content":"say it works and nothing else."}
    ]
    print(get_response(test_messages))