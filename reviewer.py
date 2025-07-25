import os
import json
import openai
from dotenv import load_dotenv
from prompt_designer import system_prompt_designer, user_prompt_designer, constraint_templates

load_dotenv()

class Reviewer:
    def __init__(self, question_obj: dict, constraints: list):
        self.question_obj = question_obj
        self.constraints = constraints
        self.question_id = question_obj["question_id"]
        self.question = question_obj["question"]
        self.output_dir = "reviewer_outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def call(self) -> list:
        constraints_desc = build_constraints_desc(self.constraints, constraint_templates)
        user_content = user_prompt_reviewer.format(
            schema=self.schema,
            question=self.question,
            evidence=self.evidence,
            gold_sql=self.gold_sql,
            constraints_desc=constraints_desc
        )
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.deepseek.com/v1")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt_reviewer},
                {"role": "user", "content": user_content}
            ],
            response_format={
                'type': 'json_object'
            }
        )
        response_content = response.choices[0].message.content
        try:
            review = json.loads(response_content)
            if not isinstance(review, list):
                raise ValueError("Rubric JSON is not an array")
        except json.JSONDecodeError as e:
            print(response_content)
            raise ValueError(f"Response is not valid JSON: {e}")

        filename = os.path.join(self.output_dir, f"{self.question_id}_review.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(review, f, ensure_ascii=False, indent=2)
            
        return review


def build_constraints_desc(constraints, templates):
    desc_lines = []
    line_no = 1

    for item in constraints:
        qid = str(item.get("question_id"))
        answers = item.get("answer")
        if answers == "NA":
            continue
        template = templates.get(qid)
        for ans in answers:
            desc_lines.append(f"{line_no}. " + template.format(answer=str(ans)))
            line_no += 1
    return "\n".join(desc_lines)

