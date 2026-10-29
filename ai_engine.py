
import os
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-2.5-flash"


def generate_sql(question):
    prompt = f"""
You are an expert MySQL query generator.

Database: ai_sales_db
Table: sales

Columns:
- sale_id: integer
- order_date: date
- product: product name
- category: product category
- quantity: number of units sold
- unit_price: price per unit
- region: sales region

Rules:
1. Convert the user's question into a MySQL SELECT query.
2. Use only the sales table and its listed columns.
3. Never generate INSERT, UPDATE, DELETE, DROP,
   ALTER, CREATE, or other modification statements.
4. Do not use joins, subqueries, UNION, or multiple statements.
5. Use LIMIT 100 for queries returning individual records.
6. For sales revenue, calculate
   SUM(quantity * unit_price).
7. Return only the SQL query, without Markdown.
8. If the question is unrelated to the database,
   return INVALID.

User question:
{question}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    if not response.text:
        raise ValueError("The AI returned an empty response.")

    query = response.text.strip()

    # Remove a Markdown code fence if the model adds one.
    query = re.sub(r"^```(?:sql)?\s*", "", query, flags=re.I)
    query = re.sub(r"\s*```$", "", query).strip()

    return validate_sql(query)


def validate_sql(query):
    query = query.strip()

    if query.upper() == "INVALID":
        raise ValueError(
            "Please ask a question related to the sales database."
        )

    # Reject multiple SQL statements.
    if ";" in query.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed.")

    query = query.rstrip(";").strip()

    # Only SELECT is allowed.
    if not re.match(r"^SELECT\b", query, flags=re.I):
        raise ValueError("Only SELECT queries are allowed.")

    # Reject comments and dangerous SQL features.
    forbidden = re.compile(
        r"--|/\*|\*/|#|\b("
        r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|"
        r"REPLACE|GRANT|REVOKE|CALL|EXEC|EXECUTE|"
        r"INTO|OUTFILE|DUMPFILE|LOAD_FILE|SLEEP|BENCHMARK|"
        r"UNION|INFORMATION_SCHEMA|JOIN|WITH"
        r")\b",
        flags=re.I
    )

    if forbidden.search(query):
        raise ValueError("The generated SQL contains a blocked operation.")

    # Only allow the sales table.
    table_names = re.findall(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        query,
        flags=re.I
    )

    if not table_names or any(
        name.lower() != "sales" for name in table_names
    ):
        raise ValueError("Only the sales table can be queried.")

    return query
