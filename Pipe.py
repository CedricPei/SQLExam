import sqlparse
from typing import Dict, Any
from helper import get_db_info
from ConstraintExtractor import ConstraintExtractor
from RubricDesigner import RubricDesigner
from RubricGrader import RubricGrader

class SQLEvaluationPipeline:
    def __init__(self, model: str = "deepseek-chat"):
        self.model = model
        self.results = []
    
    def eval(self, question: Dict[str, Any], pred_sql: str) -> float:
        try:
            question_obj = {
                "question_id": question["question_id"],
                "db_id": question["db_id"],
                "question": question["question"],
                "evidence": question.get("evidence", ""),
                "gold_sql": sqlparse.format(question["gold_sql"], reindent=True, keyword_case='upper'),
                "schema": get_db_info(question["db_id"], question["gold_sql"])
            }
            
            constraint_extractor = ConstraintExtractor(question_obj, model=self.model)
            constraints = constraint_extractor.call()
            
            rubric_designer = RubricDesigner(question_obj, constraints, model=self.model)
            designed_rubric = rubric_designer.call()
            
            rubric_grader = RubricGrader(question_obj, designed_rubric, model=self.model)
            grading_results = rubric_grader.call(pred_sql)
            
            usefulness_score = self._calculate_usefulness_score(grading_results, designed_rubric)
            return usefulness_score
            
        except Exception as e:
            print("Error in evaluation pipeline", e)

    def _calculate_usefulness_score(self, grading_results, rubric_questions):
        total_score = sum(float(r["score"]) for r in grading_results)
        total_weight = sum(float(q["weight"]) for q in rubric_questions)
        return round(total_score / total_weight, 4) if total_weight > 0 else 0.0