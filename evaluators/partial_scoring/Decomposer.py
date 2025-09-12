import os
import json
import openai
from dotenv import load_dotenv
from prompts.prompt_decomposer import system_prompt_decomposer, user_prompt_decomposer
from ..utils import extract_json_from_response, save_json

load_dotenv()

class Decomposer:
    def __init__(self, question_obj: dict, output_dir: str = "decomposer_outputs", model: str = "deepseek-chat"):
        self.model = model
        self.schema = question_obj["schema"]
        self.question_id = question_obj["question_id"]
        self.question = question_obj["question"]
        self.evidence = question_obj["evidence"]
        self.gold_sql = question_obj["gold_sql"]
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def call(self) -> list:
        user_content = user_prompt_decomposer.format(
            schema=self.schema,
            question=self.question, 
            evidence=self.evidence,
            gold_sql=self.gold_sql
        )
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt_decomposer},
                {"role": "user", "content": user_content}
            ],
            temperature=0
        )
        response_content = response.choices[0].message.content

        try:
            answer = extract_json_from_response(response_content)
            constraints = json.loads(answer)
            if not isinstance(constraints, list):
                print(response_content)
                raise ValueError("Response JSON is not an array")
        except json.JSONDecodeError as e:
            print(response_content)
            raise ValueError(f"Response is not valid JSON: {e}")

        filename = os.path.join(self.output_dir, f"{self.question_id}_constraints.json")
        save_json(constraints, filename, append=False)

        return constraints


