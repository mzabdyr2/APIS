import openai
from llm_client import get_response
from logger_config import setup_logger

MAX_HISTORY = 20
logger = setup_logger()

class Chatbot:
    def __init__(self, system_prompt: str = "You are a helpful assistant."):
        self.system_prompt = system_prompt
        self.history = []
        logger.info("Chatbot zainicjalizowany")

    def _build_messages(self) -> list[dict]:
        trimmed = self.history[-MAX_HISTORY:]
        if len(self.history) > MAX_HISTORY:
            logger.warning(f"Historia przycięta z {len(self.history)} do {MAX_HISTORY} wiadomości")
        return [{"role": "system", "content": self.system_prompt}] + trimmed

    def chat(self, user_message: str) -> str:
        # walidacja inputu
        if not user_message or not user_message.strip():
            logger.warning("Otrzymano puste zapytanie")
            return "Proszę wpisz wiadomość."

        logger.info(f"Zapytanie użytkownika: {user_message[:50]}...")  # pierwsze 50 znaków
        self.history.append({"role": "user", "content": user_message})

        try:
            messages = self._build_messages()
            response = get_response(messages)

            if not response:
                raise ValueError("Model zwrócił pustą odpowiedź")

            self.history.append({"role": "assistant", "content": response})
            logger.info("Odpowiedź wygenerowana pomyślnie")
            return response

        except openai.APIConnectionError:
            logger.error("Brak połączenia z Ollama – czy serwer działa?")
            self.history.pop()  # cofamy wiadomość użytkownika bo nie dostaliśmy odpowiedzi
            return "Błąd: nie można połączyć się z modelem."

        except openai.APIStatusError as e:
            logger.error(f"Błąd API: {e.status_code} – {e.message}")
            self.history.pop()
            return f"Błąd API: {e.status_code}"

        except ValueError as e:
            logger.error(f"Nieoczekiwana odpowiedź modelu: {e}")
            self.history.pop()
            return "Błąd: model zwrócił nieprawidłową odpowiedź."

if __name__ == "__main__":
    bot = Chatbot()
    print(bot.chat("Cześć"))
    print(bot.history)