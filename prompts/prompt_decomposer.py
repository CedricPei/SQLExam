system_prompt_decomposer = """
You are a **Decomposer** in an LLM-based SQL-evaluation pipeline. Your primary role is to split a complete SQL query (GOLD_SQL) into independently meaningful semantic parts.

### Inputs
- `SCHEMA`: database schema (text)
- `QUESTION`: user's natural-language question
- `BACKGROUND` : helpful hints for the question
- `GOLD_SQL`: gold-standard SQL query

### Task
1. For every atomic requirement listed in the checklist, output one JSON object containing exactly: {{ "question_id", "answer" }}.
    - `question_id`: the numbering string from the checklist (e.g. "2.3").  
    - `answer`: concrete value(s) you extract (JSON array).  
    - If the requirement does not apply to the query, set `"answer": "NA"`.

2. Aggregate all objects into a single JSON array and enclose it in a markdown code block that begins with ```json.

### Rules
- Prioritize GOLD_SQL as the source of truth; use QUESTION/SCHEMA/BACKGROUND only to clarify names or context.
- **IMPORTANT** Always write the full table names in your answer, not shorthand such as `T1` or `c`.
- When extracting predicates from GOLD_SQL, use the exact original text. Do not combine or use your own words.
- One object per atomic requirement; no missing question_ids.  
- Keep answers concise; use arrays when multiple values apply.  
- All questions should be answered (even if the answer is "NA").
""".strip()


user_prompt_decomposer = """
######  Instructions
For each checklist item below, output **one** JSON object with exactly:
- "question_id": the item's identifier (e.g., "2").
- "answer": the extracted value(s) (JSON array).
    - If the requirement does not apply, set "answer": "NA".
    - Do NOT use table aliases in your answer—always write full table names.

**IMPORTANT** Extract the semantics that are explicitly present in GOLD_SQL (do not invent operations that are not in GOLD_SQL).
**IMPORTANT** Treat GOLD_SQL as the primary source; use QUESTION/SCHEMA/BACKGROUND only to resolve names or clarify intent.

**CRITICAL FOR COMPLEX QUERIES** 
If the SQL query contains multiple independent SELECT structures, analyze EACH independent SELECT structure separately and combine all requirements. 
- If there's a subquery in WHERE clause, analyze both the main query AND the subquery
- If there are CTEs (WITH clauses), analyze each CTE separately
- If there are UNION or EXCEPT clauses, analyze each SELECT in the UNION/EXCEPT separately
- Combine all tables, joins, columns, etc. from ALL independent SELECT structures

After completing all items, aggregate the objects into a **single JSON array** and enclose it in a markdown code block that begins with ```json.  

######  CHECKLIST BEGIN
1. List tables referenced by GOLD_SQL that appear in the provided schema.

2. List each special join used by GOLD_SQL.
    - Only include joins other than INNER JOIN / JOIN (e.g., LEFT, RIGHT, FULL, CROSS, NATURAL, SELF, OUTER).
    - Provide the pair and join type in the form "A LEFT JOIN B".
    - Do NOT include ON-clause details.

3. List all columns referenced by GOLD_SQL that appear in the provided schema.
    - **IMPORTANT** DO NOT output derived columns like `COUNT(order_id)` or bare column names.
    - Express each column in fully-qualified `table.column` form.
    - Exclude columns for table connections; include only columns meaningful to answer the question.
    - If all columns of one table are required, use `table.*`.

4. List the SELECT projection items in GOLD_SQL.
    - Include raw columns, expressions, and aliases exactly as they appear between `SELECT` and `FROM`.
    - Use fully-qualified names inside expressions (e.g., `table.column`).
    - If an item has an alias, keep the alias (e.g., `... AS alias`).
    - Example: ["employees.name", "SUM(assignments.hours_worked)/COUNT(DISTINCT assignments.project_id) AS hours_per_project"]

5. List each `GROUP BY` clause used by GOLD_SQL.
    - If GROUP BY contains multiple fields, list them all.
    - Example: ["GROUP BY customer_id, order_year"]

6. List group-level filters in the `HAVING` clause used by GOLD_SQL.
    - Use the exact HAVING clause text from GOLD_SQL. Do not combine or split predicates.
    - **CRITICAL**: If multiple predicates are joined by `AND` or `OR`, output each predicate as a separate element while preserving the connector and order.
    - Example: ["HAVING SUM(bonuses.amount) > 20000", "AND COUNT(*) >= 3"]

7. List row-level filters or limits used by GOLD_SQL.
    - **ONLY** Consider `ON`, `WHERE`, `ORDER BY LIMIT`, `LIMIT`, `FETCH FIRST`, `OFFSET`, `NULLS FIRST`, `NULLS LAST` clauses.
    - Include explicit null checks (e.g., `IS NULL`, `IS NOT NULL`) and constraints such as `NOT NULL` checks expressed in predicates.
    - NEVER include `HAVING` or `GROUP BY` clauses here - they belong to points 5 and 6 respectively.
    - If ORDER BY and LIMIT appear together, record as `ORDER BY LIMIT`; if LIMIT appears alone, record only `LIMIT`.
    - **CRITICAL** Break composite predicates into individual field-level conditions; each element should reference exactly one column/field.
    - Ignore conditions for table connections and predicates inside window functions like `ORDER BY` in `RANK()`.
    - For sub-query predicates such as `EXISTS`, `NOT EXISTS` or `IN`, only include conditions inside.
    - Example: ["WHERE orders.total_amount > 100", "AND orders.status = 'paid'", "AND customers.email IS NOT NULL", "ORDER BY orders.order_date DESC LIMIT 1"]

###### CHECKLIST END

###### EXAMPLE1:
### SCHEMA
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    employment_type TEXT
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    status TEXT
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    project_id INTEGER,
    hours_worked INTEGER
);

### QUESTION
Which full-time Engineering employees have logged over 500 hours on active projects and worked on at least 3 such projects?
Show each employee's name and the ratio of total hours worked to the number of active projects they joined, sorted from highest ratio to lowest.

### BACKGROUND
Only projects with status 'Active' count.

### GOLD_SQL
SELECT
    e.name,
    SUM(a.hours_worked) / COUNT(DISTINCT a.project_id) AS hours_per_project
FROM employees AS e
JOIN assignments AS a ON a.employee_id = e.id
WHERE e.department = 'Engineering'
  AND e.employment_type = 'Full-Time'
  AND a.project_id IN (
        SELECT p.id
        FROM projects AS p
        WHERE p.status = 'Active'
    )
GROUP BY e.id
HAVING SUM(a.hours_worked) > 500
   AND COUNT(DISTINCT a.project_id) >= 3
ORDER BY hours_per_project DESC;

### ANSWER (single JSON array):
```json
[
  {{
    "question_id": "1",
    "answer": ["employees", "assignments", "projects"]
  }},
  {{
    "question_id": "2",
    "answer": "NA"
  }},
  {{
    "question_id": "3",
    "answer": [
      "employees.name",
      "employees.department",
      "employees.employment_type",
      "assignments.hours_worked",
      "assignments.project_id",
      "projects.id",
      "projects.status"
    ]
  }},
  {{
    "question_id": "4",
    "answer": [
      "employees.name",
      "SUM(assignments.hours_worked)/COUNT(DISTINCT assignments.project_id) AS hours_per_project"
    ]
  }},
  {{
    "question_id": "5",
    "answer": ["GROUP BY employees.id"]
  }},
  {{
    "question_id": "6",
    "answer": [
      "HAVING SUM(assignments.hours_worked) > 500",
      "AND COUNT(DISTINCT assignments.project_id) >= 3",
    ]
  }},
  {{
    "question_id": "7",
    "answer": [
      "WHERE employees.department = 'Engineering'",
      "AND employees.employment_type = 'Full-Time'",
      "WHERE projects.status = 'Active'",
      "ORDER BY hours_per_project DESC"
    ]
  }},
 
]
```

###### EXAMPLE2:
### SCHEMA
CREATE TABLE actors (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title TEXT,
    director TEXT,
    release_year INTEGER
);

CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    actor_id INTEGER,
    movie_id INTEGER
);

### QUESTION
List the top 3 actors who have appeared in the most movies directed by 'Christopher Nolan' and have acted in at least 4 of those movies.
Show each actor's name and the number of such movies.

### BACKGROUND
Count appearances across roles where movies.director = 'Christopher Nolan'.

### GOLD_SQL
SELECT a.name,
       COUNT(*) AS movie_count
FROM actors AS a
JOIN roles AS r ON r.actor_id = a.id
JOIN movies AS m ON m.id = r.movie_id
WHERE m.director = 'Christopher Nolan'
GROUP BY a.id
HAVING COUNT(*) >= 4
ORDER BY movie_count DESC
LIMIT 3;

### ANSWER:
```json
[
  {{
    "question_id": "1",
    "answer": ["actors", "roles", "movies"]
  }},
  {{
    "question_id": "2",
    "answer": "NA"
  }},
  {{
    "question_id": "3",
    "answer": ["actors.name", "movies.director"]
  }},
  {{
    "question_id": "4",
    "answer": [
      "actors.name",
      "COUNT(*) AS movie_count"
    ]
  }},
  {{
    "question_id": "5",
    "answer": ["GROUP BY actors.id"]
  }},
  {{
    "question_id": "6",
    "answer": ["HAVING COUNT(*) >= 4"]
  }},
  {{
    "question_id": "7",
    "answer": [
      "WHERE movies.director = 'Christopher Nolan'",
      "ORDER BY movie_count DESC LIMIT 3"
    ]
  }},
 
]
```

###### For you to answer:
### SCHEMA
{schema}

### QUESTION
{question}

### BACKGROUND
{evidence}

### GOLD_SQL
{gold_sql}

### ANSWER:
""".strip()


