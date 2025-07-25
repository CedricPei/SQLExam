import os
import json
import openai
from dotenv import load_dotenv
from prompt_observer import system_prompt_observer, user_prompt_observer
from utils import extract_json_from_response

load_dotenv()

class Observer:
    def __init__(self, question_obj: dict, output_dir: str = "obs_outputs"):
        self.schema = question_obj["schema"]
        self.question_id = question_obj["question_id"]
        self.question = question_obj["question"]
        self.evidence = question_obj["evidence"]
        self.gold_sql = question_obj["gold_sql"]
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def call(self) -> list:
        user_content = user_prompt_observer.format(
            schema=self.schema,
            question=self.question, 
            evidence=self.evidence,
            gold_sql=self.gold_sql
        )
        # print(user_content)
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.deepseek.com/v1")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt_observer},
                {"role": "user", "content": user_content}
            ],
            response_format={
                'type': 'json_object'
            }
        )
        response_content = response.choices[0].message.content

        try:
            answer = extract_json_from_response(response_content)
            constraints = json.loads(answer)
            if not isinstance(constraints, list):
                raise ValueError("Response JSON is not an array")
        except json.JSONDecodeError as e:
            print(response_content)
            raise ValueError(f"Response is not valid JSON: {e}")

        filename = os.path.join(self.output_dir, f"{self.question_id}_obs.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(constraints, f, ensure_ascii=False, indent=2)

        return constraints
