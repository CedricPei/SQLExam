import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any
from helper import get_schema, extract_json_from_response, append_to_json_file
from prompts.prompt_prover import system_prompt_prover, user_prompt_prover

load_dotenv()


class Prover:
    """Prover validates whether predicted SQL queries adequately answer given questions"""
    
    def __init__(self, model: str = None):
        self.model = model
    
    def call(self, question: Dict[str, Any], pred_sql: str, pred_result: Any) -> bool:
        """Validate whether predicted SQL adequately answers the question"""
        try:
            schema = get_schema(question["db_id"])
            pred_result = pred_result.head(20)
            
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
            # Save output to a single JSON file (append mode)
            output_data = {
                "question_id": question["question_id"],
                "result": result
            }
            append_to_json_file(output_data, "output/prover_output.json")

            return result.get("verdict", False)

        except Exception as e:
            print(f"Prover error: {e}")
            return False
