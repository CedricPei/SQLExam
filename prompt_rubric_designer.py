system_prompt_rubric_designer = """
You are **SQL Rubric Designer**, a component that designs evaluation rubrics for SQL constraints.
Your task is to convert the constraint descriptions into clear, evaluable questions with assigned weights.

### Inputs
  - constraint_descriptions: JSON array with descriptions and weighting rules for each constraint
  - schema: the database schema as CREATE TABLE statements
  - question: the original natural language question

### Task
1. For each constraint description, generate a natural language question that can be used to evaluate whether a SQL query meets the constraint
2. Assign a weight based on the constraint type and importance
3. Provide a brief explanation of how to assign points (1-2 sentences) before the weight
4. Output a JSON array with objects containing:
   - question_id: string — the original question_id from the constraint
   - question: string — the natural language question
   - weighting_explanation: string — brief explanation of how to assign points for this question
   - weight: number — the point value for this question

### Rules
- Keep questions clear and specific using natural language
- Use consistent weighting based on constraint type
- Make questions evaluable (yes/no or specific answer format)
- Preserve the original question_id from the constraint
- Use natural language for column references (e.g., "column `name` in table `customers`")
"""

user_prompt_rubric_designer = """
###### Instructions
Design evaluation rubrics by translating constraint descriptions into natural language questions. Each constraint should become a clear question that can be used to assess whether a generated SQL query meets the requirement.

For each constraint, create a JSON object with:
- "question_id": the original question_id from the constraint
- "question": natural language question
- "weighting_explanation": brief explanation of how to assign points for this question
- "weight": point value based on constraint type

Aggregate all objects into a single JSON array.

###### EXAMPLE
### ORIGINAL QUESTION:
"List the names of customers who have placed at least one order."

### SCHEMA:
CREATE TABLE customers (
  id INT PRIMARY KEY,
  name TEXT
);

CREATE TABLE orders (
  id INT PRIMARY KEY,
  customer_id INT,
  total DECIMAL
);

### CONSTRAINT DESCRIPTIONS:
[
  {
    "question_id": "1",
    "description": "To build the SQL query to answer the question, customers is compulsory",
    "weighting_rule": "Each table one point"
  },
  {
    "question_id": "1",
    "description": "To build the SQL query to answer the question, orders is compulsory", 
    "weighting_rule": "Each table one point"
  },
  {
    "question_id": "3",
    "description": "To build the SQL query to answer the question, the column customers.name is compulsory",
    "weighting_rule": "Each column one point"
  }
]

### DESIGNED RUBRIC:
```json
[
  {
    "question_id": "1",
    "question": "Does the generated SQL query use the customers table?",
    "weighting_explanation": "Each table used in the query receives one point.",
    "weight": 1
  },
  {
    "question_id": "1", 
    "question": "Does the generated SQL query use the orders table?",
    "weighting_explanation": "Each table used in the query receives one point.",
    "weight": 1
  },
  {
    "question_id": "3",
    "question": "Does the generated SQL query select the column `name` in table `customers`?",
    "weighting_explanation": "Each required column selected in the query receives one point.",
    "weight": 1
  }
]
```

###### For you to design:
### ORIGINAL QUESTION:
{question}

### SCHEMA:
{schema}

### CONSTRAINT DESCRIPTIONS:
{constraint_descriptions}

### DESIGNED RUBRIC:
"""

rubric_templates = {
  # 1. tables
  "1": {
    "description": "To build the SQL query to answer the question, {answer} is compulsory",
    "weighting_rule": "Each table one point"
  },
  
  # 2. joins
  "2": {
    "description": "To build the SQL query to answer the question, the join {answer} is compulsory",
    "weighting_rule": "Each join one point"
  },
  
  # 3. columns
  "3": {
    "description": "To build the SQL query to answer the question, the column {answer} is compulsory",
    "weighting_rule": "Each column one point"
  },
  
  # 4. aggregate functions
  "4": {
    "description": "To build the SQL query to answer the question, the aggregate function {answer} is compulsory",
    "weighting_rule": "Each aggregate function one point"
  },
  
  # 5. row-level filters / limits
  "5": {
    "description": "To build the SQL query to answer the question, the filter {answer} is compulsory",
    "weighting_rule": "Each filter one point"
  },
  
  # 6. GROUP BY clauses
  "6": {
    "description": "To build the SQL query to answer the question, the GROUP BY {answer} is compulsory",
    "weighting_rule": "Each GROUP BY clause one point"
  },
  
  # 7. HAVING clauses
  "7": {
    "description": "To build the SQL query to answer the question, the HAVING {answer} is compulsory",
    "weighting_rule": "Each HAVING clause one point"
  },
  
  # 8. unique columns
  "8": {
    "description": "To build the SQL query to answer the question, the uniqueness on {answer} is compulsory",
    "weighting_rule": "Each uniqueness requirement one point"
  },
  
  # 9. output format details
  "9": {
    "description": "To build the SQL query to answer the question, the format requirement {answer} is compulsory",
    "weighting_rule": "Each format requirement one point"
  }
} 