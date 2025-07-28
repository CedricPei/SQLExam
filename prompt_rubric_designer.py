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
- Keep questions clear and specific using natural language
- Use consistent weighting based on constraint type
- Make questions evaluable (yes/no or specific answer format)
- Use natural language for column references (e.g., "column `name` in table `customers`")
"""

user_prompt_rubric_designer = """
###### Instructions
Design evaluation rubrics by translating constraint descriptions into natural language questions. Each constraint should become a clear question that can be used to assess whether a generated SQL query meets the requirement.

For each constraint, create a JSON object with:
- "question": natural language question
- "explanation": brief explanation of how to assign points for this question
- "weight": point value based on constraint type

Aggregate all objects into a single JSON array.

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
SELECT a.name, COUNT(*) AS movie_count FROM actors AS a JOIN roles AS r ON r.actor_id = a.id JOIN movies AS m ON m.id = r.movie_id WHERE m.director = 'Christopher Nolan' GROUP BY a.id ORDER BY movie_count DESC LIMIT 1;

### CONSTRAINT DESCRIPTIONS
```json
[
  {
    "description": "The SQL query must reference the table: actors.",
    "weighting_rule": "Give one point for each required table."
  },
  {
    "description": "The SQL query must reference the table: movies.",
    "weighting_rule": "Give one point for each required table."
  },
  {
    "description": "The SQL query must reference the table: roles.",
    "weighting_rule": "Give one point for each required table."
  },
  {
    "description": "The SQL query must include the join: actors JOIN roles ON roles.actor_id = actors.id.",
    "weighting_rule": "Give one point for the required join between the specified tables; For joins other than NATURAL JOIN or CROSS JOIN, give one point for each independent ON clause condition; If the specified join type is not INNER, award one additional point for using that join type."
  },
  {
    "description": "The SQL query must include the join: roles JOIN movies ON movies.id = roles.movie_id.",
    "weighting_rule": "Give one point for the required join between the specified tables; For joins other than NATURAL JOIN or CROSS JOIN, give one point for each independent ON clause condition; If the specified join type is not INNER, award one additional point for using that join type."
  },
  {
    "description": "The SQL query must reference the column: actors.name.",
    "weighting_rule": "Assign one point for each required column."
  },
  {
    "description": "The SQL query must satisfy the row-level requirement: WHERE movies.director = 'Christopher Nolan'.",
    "weighting_rule": "Award one point for each predicate in the WHERE clause; Credit one point for each sort key in ORDER BY; Add one point when ORDER BY specifies a direction other than ASC; Give one point for each row-limit directive such as LIMIT or OFFSET."
  },
  {
    "description": "The SQL query must satisfy the row-level requirement: ORDER BY movie_count DESC.",
    "weighting_rule": "Award one point for each predicate in the WHERE clause; Credit one point for each sort key in ORDER BY; Add one point when ORDER BY specifies a direction other than ASC; Give one point for each row-limit directive such as LIMIT or OFFSET."
  },
  {
    "description": "The SQL query must satisfy the row-level requirement: LIMIT 1.",
    "weighting_rule": "Award one point for each predicate in the WHERE clause; Credit one point for each sort key in ORDER BY; Add one point when ORDER BY specifies a direction other than ASC; Give one point for each row-limit directive such as LIMIT or OFFSET."
  },
  {
    "description": "The SQL query must group results by: GROUP BY actors.id.",
    "weighting_rule": "Award one point for each field listed in GROUP BY."
  }
]
```

### DESIGNED RUBRIC:
```json
[
  {
    "question": "Does the query read from the `actors` table?",
    "explanation": "Presence of this table yields one point.",
    "weight": 1
  },
  {
    "question": "Is the `movies` table included in the query?",
    "explanation": "Presence of this table yields one point.",
    "weight": 1
  },
  {
    "question": "Does the query reference the `roles` table?",
    "explanation": "Presence of this table yields one point.",
    "weight": 1
  },
  {
    "question": "Is there a join between `roles` and `actors` on matching actor IDs?",
    "explanation": "One point for the join plus one for the correct ON condition.",
    "weight": 2
  },
  {
    "question": "Does the query join `roles` to `movies` using movie IDs?",
    "explanation": "One point for the join plus one for the correct ON condition.",
    "weight": 2
  },
  {
    "question": "Is the actor's identifier (`actors.name` or `actors.id`) selected in the output?",
    "explanation": "Referencing this required column earns one point.",
    "weight": 1
  },
  {
    "question": "Does the query filter for movies directed by Christopher Nolan?",
    "explanation": "Each predicate in the WHERE clause is worth one point.",
    "weight": 1
  },
  {
    "question": "Are results ordered by movie count in descending order?",
    "explanation": "One point for the correct sort key and one point for specifying descending direction.",
    "weight": 2
  },
  {
    "question": "Is the result limited to only the top actor?",
    "explanation": "Limiting the output to one row earns one point.",
    "weight": 1
  },
  {
    "question": "Does the query group the rows so that each actor's movies are aggregated together?",
    "explanation": "Each grouping key required is worth one point.",
    "weight": 1
  }
]
```

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
```json
{constraint_descriptions}
```

### DESIGNED RUBRIC:
"""

rubric_templates = {
    # 1. required tables
    "1": {
        "description": "The SQL query must reference the table: {answer}.",
        "weighting_rule": "Give one point for each required table."
    },
    
    # 2. required joins
    "2": {
        "description": "The SQL query must include the join: {answer}.",
        "weighting_rule": "Give one point for the required join between the specified tables; For joins other than NATURAL JOIN or CROSS JOIN, give one point for each independent ON clause condition; If the specified join type is not INNER, award one additional point for using that join type."
    },
    
    # 3. required columns
    "3": {
        "description": "The SQL query must reference the column: {answer}.",
        "weighting_rule": "Assign one point for each required column."
    },
    
    # 4. required aggregate functions
    "4": {
        "description": "The SQL query must apply the aggregate function: {answer} in the SELECT clause.",
        "weighting_rule": "Give one point for every aggregate function present; if an expression contains several aggregates, credit as many points as the number of aggregate functions."
    },
    
    # 5. required row‑level filters and limits
    "5": {
        "description": "The SQL query must satisfy the row-level requirement: {answer}.",
        "weighting_rule": "Award one point for each predicate in the WHERE clause; Credit one point for each sort key in ORDER BY; Add one point when ORDER BY specifies a direction other than ASC; Give one point for each row-limit directive such as LIMIT or OFFSET."
    },
    
    # 6. required GROUP BY clauses
    "6": {
        "description": "The SQL query must group results by: {answer}.",
        "weighting_rule": "Award one point for each field listed in GROUP BY."
    },
    
    # 7. required HAVING clauses
    "7": {
        "description": "The SQL query must include a HAVING condition: {answer}.",
        "weighting_rule": "Assign one point for each condition in the HAVING clause."
    },
    
    # 8. uniqueness requirements
    "8": {
        "description": "The SQL query must ensure uniqueness for {answer}.",
        "weighting_rule": "Give one point for each column that must be unique."
    },
    
    # 9. output‑format requirements
    "9": {
        "description": "The result set must meet the output-format requirement: {answer}.",
        "weighting_rule": "Award one point for each formatting directive."
    }
}
