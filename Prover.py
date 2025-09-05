import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any
from helper import get_schema, extract_json_from_response
from prompt_prover import system_prompt_prover, user_prompt_prover

load_dotenv()


class Prover:
    """Prover validates whether predicted SQL queries adequately answer given questions"""
    
    def __init__(self, model: str = None):
        self.model = model
    
    def call(self, question: Dict[str, Any], pred_sql: str, pred_result: Any) -> bool:
        """Validate whether predicted SQL adequately answers the question"""
        try:
            schema = get_schema(question["db_id"])
            
            user_content = user_prompt_prover.format(
                question=question["question"],
                evidence=question.get("evidence", ""),
                predicted_sql=pred_sql,
                schema=schema,
                sql_result=pred_result
            )
            
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_prover},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )

            result = json.loads(extract_json_from_response(response.choices[0].message.content))
            # Save output to JSON file
            os.makedirs("prover_outputs", exist_ok=True)
            with open(f"prover_outputs/prover_{question['question_id']}.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            return result.get("verdict", False)

        except Exception as e:
            print(f"Prover error: {e}")
            return False
