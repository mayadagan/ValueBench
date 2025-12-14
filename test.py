from pydantic import BaseModel
from all_the_llms import LLM
from dotenv import load_dotenv
from prompt_manager import PromptManager

load_dotenv()

class Rating(BaseModel):
    rating: int
    review: str

llm = LLM("gpt-4o")

pm = PromptManager()

user_data = {
    "code_snippet": "def login(user, pass):\n    print(pass)\n    return True",
    "focus_areas": ["Security Risks", "Python Standards"]
}

prompt = pm.build("workflows/code_review/main.yaml", user_data)

user = llm.structured_completion(
    messages=prompt["messages"],
    response_model=Rating
)
print(user.rating)
print(user.review)