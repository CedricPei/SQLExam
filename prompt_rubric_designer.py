system_prompt_rubric_designer = """
You are **SQL Rubric Designer**, a component that designs evaluation rubrics for SQL constraints.
Your task is to convert the constraint descriptions into clear, evaluable natural language questions with assigned weights.

### Inputs
  - constraint_descriptions: JSON array with descriptions and weighting rules for each constraint
  - schema: the database schema as CREATE TABLE statements
  - question: the original natural language question
  - background: helpful hints for the question
  - gold_sql: the ground truth SQL query (for reference only)

### Task
1. For each constraint description, generate a natural language question that can be used to evaluate whether a SQL query meets the constraint
2. Assign a weight based on the constraint type and importance
3. Provide a brief explanation of how to assign points (1-2 sentences) before the weight
4. Output a JSON array with objects containing:
   - question: string — the natural language question
   - explanation: string — brief explanation of how to assign points for this question
   - weight: number — the point value for this question

### Rules
- Make questions clear, evaluable and specific to the actual context in the original question.
- **IMPORTANT**: Use natural language throughout, avoid SQL syntax and symbols
    - Instead of "table.column", use "column [column_name] of the table [table_name]"
    - Instead of SQL functions like COUNT, SUM, etc., use natural language like "count", "sum", "average"
    - Avoid using backticks, SQL keywords, or technical SQL syntax in questions
    - For set operators, ask about meaning rather than syntax
      - For example, "Does the query combine students from both computer science and mathematics departments?" instead of "Does the query use UNION?"
- Try different question phrasing.
- Return ONLY the JSON array, do not wrap it in any object or add any keys
"""

user_prompt_rubric_designer = """
###### Instructions
Design evaluation rubrics by translating constraint descriptions into natural language questions. Each constraint should become a clear question that can be used to assess whether a generated SQL query meets the requirement.

For each constraint, create a JSON object with:
- "question": natural language question
- "explanation": brief explanation of how to assign points for this question
- "weight": point value based on constraint type

After designing all questions from the constraints, aggregate all objects into a single JSON array. Return ONLY the JSON array directly, do not wrap it in any object or add any keys.
**IMPORTANT**: Use natural language throughout. Avoid SQL syntax, symbols, and technical terms. 

###### EXAMPLE
### QUESTION
Which actor has appeared in the greatest number of movies directed by Christopher Nolan?

### SCHEMA
CREATE TABLE actors (
  id   INT PRIMARY KEY,
  name TEXT
);

CREATE TABLE movies (
  id       INT PRIMARY KEY,
  title    TEXT,
  director TEXT
);

CREATE TABLE roles (
  actor_id  INT,
  movie_id  INT,
  FOREIGN KEY (actor_id) REFERENCES actors(id),
  FOREIGN KEY (movie_id) REFERENCES movies(id)
);

### BACKGROUND
Christopher Nolan is identified by the condition movies.director = 'Christopher Nolan'; The greatest number of movies is obtained by taking the maximum count of movies per actor; Actor names are stored in the column actors.name.

### GOLD SQL
SELECT
    a.name,
    COUNT(*) AS movie_count
FROM actors AS a
JOIN roles AS r
    ON r.actor_id = a.id
JOIN movies AS m
    ON m.id = r.movie_id
WHERE m.director = 'Christopher Nolan'
GROUP BY a.id
ORDER BY movie_count DESC
LIMIT 1;

### CONSTRAINT DESCRIPTIONS
[
  {{
    "description": "The SQL query must reference the tables: [actors, movies, roles].",
    "weighting_rule": "All required tables together contribute a maximum of one point."
  }},
  {{
    "description": "The SQL query must reference the columns: [actors.name, actors.id, movies.director].",
    "weighting_rule": "Each required column is worth 0.5 point; the combined score for this category is capped at two points."
  }},
  {{
    "description": "The SQL query must apply the function: COUNT(*) in the SELECT clause.",
    "weighting_rule": "Give one point for every function present; if an expression contains several functions, credit all of them; for window functions, add one point when a PARTITION BY clause is present and two points whenever an ORDER BY clause appears."
  }},
  {{
    "description": "The SQL query must satisfy the row-level requirement: WHERE movies.director = 'Christopher Nolan'.",
    "weighting_rule": "Assign two points for each independent predicate; add one additional point for correctly expressing the logical relationship among predicates (e.g., AND, OR)."
  }},
  {{
    "description": "The SQL query must satisfy the row-level requirement: ORDER BY movie_count DESC.",
    "weighting_rule": "Assign two points for each independent predicate; add one additional point for correctly expressing the logical relationship among predicates (e.g., AND, OR)."
  }},
  {{
    "description": "The SQL query must satisfy the row-level requirement: LIMIT 1.",
    "weighting_rule": "Assign two points for each independent predicate; add one additional point for correctly expressing the logical relationship among predicates (e.g., AND, OR)."
  }},
  {{
    "description": "The SQL query must group results by: GROUP BY actors.id.",
    "weighting_rule": "The first required grouping key is worth one point; each additional grouping key earns 0.5 point; the total for this category is capped at two points."
  }}
]

### OUTPUT (return ONLY this JSON array):
[
  {{
    "question": "Does the query use the information from all three tables: actors, movies, and roles?",
    "explanation": "One point is awarded only if all three tables are used, as each provides essential context for the answer.",
    "weight": 1
  }},
  {{
    "question": "Does the query use the name and ID columns from the actors table, and the director column from the movies table?",
    "explanation": "Three required columns are used; each counts for 0.5 point, totaling 1.5 points.",
    "weight": 1.5
  }},
  {{
    "question": "Does the query count how many movies each actor has appeared in?",
    "explanation": "One point is given for correctly applying a counting operation to compute appearances.",
    "weight": 1
  }},
  {{
    "question": "Does the query only include movies directed by Christopher Nolan?",
    "explanation": "This filter is necessary to match the question intent, so it receives two points.",
    "weight": 2
  }},
  {{
    "question": "Does the query sort the results so that the actor with the highest movie count comes first?",
    "explanation": "Two points are awarded for correctly sorting in descending order of movie count.",
    "weight": 2
  }},
  {{
    "question": "Does the query select only the actor who has appeared in the most movies directed by Christopher Nolan?",
    "explanation": "Two points are given for restricting the result to a single top-ranking actor.",
    "weight": 2
  }},
  {{
    "question": "Does the query group the results by actor ID to count appearances correctly?",
    "explanation": "One point is awarded for grouping by actor ID as the sole grouping key.",
    "weight": 1
  }}
]

###### For you to design:
### QUESTION
{question}

### SCHEMA
{schema}

### BACKGROUND
{background}

### GOLD SQL
{gold_sql}

### CONSTRAINT DESCRIPTIONS
{constraint_descriptions}

### OUTPUT (return ONLY the JSON array):
"""

rubric_templates = {
  # 1. set operators
  "1": {
      "description": "The SQL query must use the set operator: {answer}.",
      "weighting_rule": "Each required set operator is worth two points."
  },

  # 2. required tables
  "2": {
      "description": "The SQL query must reference the tables: {answer}.",
      "weighting_rule": "All required tables together contribute a maximum of one point."
  },

  # 3. required joins
  "3": {
      "description": "The SQL query must include the join: {answer}.",
      "weighting_rule": "Award one point for each required join that employs a special join type other than a basic INNER JOIN."
  },

  # 4. required columns
  "4": {
      "description": "The SQL query must reference the columns: {answer}.",
      "weighting_rule": "Each required column is worth 0.5 point; the combined score for this category is capped at two points."
  },

  # 5. required functions
  "5": {
      "description": "The SQL query must apply the function: {answer} in the SELECT clause.",
      "weighting_rule": "Give one point for every function present; if an expression contains several functions, credit all of them; for window functions, add one point when a PARTITION BY clause is present and two points whenever an ORDER BY clause appears."
  },

  # 6. required row‑level filters and limits
  "6": { 
      "description": "The SQL query must satisfy the row-level filter: {answer}.",
      "weighting_rule": "Assign two points for each independent predicate; add one additional point for correctly expressing the logical relationship among predicates (e.g., AND, OR)."
  },

  # 7. required GROUP BY clauses
  "7": {
      "description": "The SQL query must group results by: {answer}.",
      "weighting_rule": "The first required grouping key is worth one point; each additional grouping key earns 0.5 point; the total for this category is capped at two points."
  },

  # 8. required HAVING clauses
  "8": {
      "description": "The SQL query must include a HAVING condition: {answer}.",
      "weighting_rule": "Each independent HAVING condition is worth two points; add one extra point for expressing the correct logical relationship among multiple conditions."
  },

  # 9. uniqueness requirements
  "9": {
      "description": "The SQL query must ensure uniqueness for {answer}.",
      "weighting_rule": "Each uniqueness requirement earns one point."
  },

  # 10. output‑format requirements
  "10": {
      "description": "The result set must meet the output-format requirement: {answer}.",
      "weighting_rule": "Each formatting requirement earns one point."
  }
}
