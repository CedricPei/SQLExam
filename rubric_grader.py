import json
import os
import openai
from dotenv import load_dotenv
from prompt_rubric_grader import system_prompt_grader, user_prompt_grader
from utils import extract_json_from_response

load_dotenv()

class RubricGrader:
    def __init__(self, question_obj: dict, rubric_questions: list, output_dir: str = "grader_outputs", model: str = "deepseek-chat"):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.deepseek.com/v1" if model == "deepseek-chat" else None)
        self.model = model
        self.schema = question_obj["schema"]
        self.question_id = question_obj["question_id"]
        self.question = question_obj["question"]
        self.evidence = question_obj["evidence"]
        self.rubric_questions = json.dumps(rubric_questions, ensure_ascii=False, indent=2)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def call(self, predicted_sql):        
        user_prompt = user_prompt_grader.format(
            question=self.question,
            schema=self.schema,
            background=self.evidence,
            rubric_questions=self.rubric_questions,
            predicted_sql=predicted_sql
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt_grader},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                'type': 'json_object'
            },
            temperature=0
        )
        response_content = response.choices[0].message.content
        
        try:
            answer = extract_json_from_response(response_content)
            grading_results = json.loads(answer)
            if not isinstance(grading_results, list):
                print(response_content)
                raise ValueError("Response JSON is not an array")
        except json.JSONDecodeError as e:
            print(response_content)
            raise ValueError(f"Response is not valid JSON: {e}")

        filename = os.path.join(self.output_dir, f"{self.question_id}_grading.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(grading_results, f, ensure_ascii=False, indent=2)            
        return grading_results