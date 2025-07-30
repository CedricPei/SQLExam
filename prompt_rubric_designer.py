system_prompt_rubric_designer = """
You are **SQL Rubric Designer**, a component that designs evaluation rubrics for SQL constraints.
Your task is to convert the constraint descriptions into clear, evaluable natural language questions with assigned weights, focusing on semantic meaning rather than syntactic form.

### Inputs
  - constraint_descriptions: JSON array with descriptions and weighting rules for each constraint
  - schema: the database schema as CREATE TABLE statements
  - question: the original natural language question
  - background: helpful hints for the question
  - gold_sql: the ground truth SQL query (for reference only)

### Task
1. **IMPORTANT**: Create exactly one question for each constraint description - there should be a one-to-one correspondence between constraints and questions
2. For each constraint description, generate a natural language question that can be used to evaluate whether a SQL query meets the constraint
3. Assign a weight based on the constraint type and importance
4. Provide a brief explanation of why to assign points (1-2 sentences)
5. Output a JSON array with objects containing:
   - question: string — the natural language question
   - explanation: string — brief explanation of why to assign points for this question
   - weight: number — the point value for this question

### Rules
- Make questions clear, evaluable and specific to the actual context in the original question.
- **IMPORTANT**: Focus on the semantic meaning of SQL constraints rather than their syntactic form
- **IMPORTANT**: Use natural language throughout, avoid SQL syntax and symbols
    - Instead of "table.column", use "column [column_name] of the table [table_name]"
    - Instead of SQL functions like COUNT, SUM, etc., use natural language like "count", "sum", "average"
    - Avoid using backticks, SQL keywords, or technical SQL syntax in questions
- Try different question phrasing.
- Return ONLY the JSON array, do not wrap it in any object or add any keys
"""

user_prompt_rubric_designer = """
###### Instructions
Design evaluation rubrics by translating constraint descriptions into natural language questions. Each constraint should become a clear question that can be used to assess whether a generated SQL query meets the requirement.

For each constraint, create a JSON object with:
- "question": natural language question
- "explanation": brief explanation of why to assign points for this question (based on the weighting rules)
- "weight": point value based on the weighting rules

After designing all questions from the constraints, aggregate all objects into a single JSON array. The order of the output JSON array must strictly match the order of the constraint descriptions.
Return ONLY the JSON array directly, do not wrap it in any object or add any keys.
**IMPORTANT**: Focus on the semantic meaning of constraints rather than their syntactic form. Use natural language throughout. Avoid SQL syntax, symbols, and technical terms. 

###### Weighting Rules:
1. Required tables
   - All required tables together contribute a maximum of one point.
2. Required joins
   - Award one point for each required join that employs a special join type other than a basic INNER JOIN.
3. Required columns
   - Each required column is worth 0.5 point; the combined score for this category is capped at two points.
4. Required functions
   - Give one point for every function present; if an expression contains several functions, credit all of them;
   - For window functions, add one point when a PARTITION BY clause is present and two points whenever an ORDER BY clause appears.
5. GROUP BY
   - The first required grouping key is worth one point; each additional grouping key earns 0.5 point; the total for this category is capped at two points.
6. HAVING
   - Assign two points for each semantically independent predicate. 
   - For compound conditions like 'HAVING A AND B', treat A and B as separate semantically independent predicates and assign 4 points total (2 points each).
7. Row-level filters/limits
   - Assign two points for each semantically independent predicate;
   - Ignore conditions only for table connections;
   - For compound conditions like 'WHERE A AND B', treat A and B as separate semantically independent predicates and assign 4 points total (2 points each).
8. Uniqueness requirements
   - Each uniqueness requirement earns one point.
9. Output-format requirements
   - Each formatting requirement earns one point.

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
1. The SQL query must reference the tables: [actors, movies, roles].
2. The SQL query must reference the columns: [actors.name, actors.id, movies.director].
3. The SQL query must apply the function: COUNT(*) in the SELECT clause.
4. The SQL query must group results by: GROUP BY actors.id.
5. The SQL query must satisfy the requirement: WHERE movies.director = 'Christopher Nolan'.
6. The SQL query must satisfy the requirement: ORDER BY movie_count DESC.
7. The SQL query must satisfy the requirement: LIMIT 1.

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
  # 1. required tables
  "1": {
      "description": "The SQL query must reference the tables: {answer}."
  },

  # 2. required joins
  "2": {
      "description": "The SQL query must include the join: {answer}."
  },

  # 3. required columns
  "3": {
      "description": "The SQL query must reference the columns: {answer}."
  },

  # 4. required functions
  "4": {
      "description": "The SQL query must apply the function: {answer} in the SELECT clause."
  },

  # 5. required GROUP BY clauses
  "5": {
      "description": "The SQL query must group results by: {answer}."
  },

  # 6. required HAVING clauses
  "6": {
      "description": "The SQL query must include a HAVING condition: {answer}."
  },

  # 7. required row‑level filters and limits
  "7": { 
      "description": "The SQL query must satisfy the requirement: {answer}."
  },

  # 8. uniqueness requirements
  "8": {
      "description": "The SQL query must ensure uniqueness for {answer}."
  },

  # 9. output‑format requirements
  "9": {
      "description": "The result set must meet the output-format requirement: {answer}."
  }
}
