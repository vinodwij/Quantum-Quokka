import re

def extract_sql_from_response(response):
    match = re.search(r"```sql\s+(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"```(.*?)```", response, re.DOTALL)
    return match.group(1).strip() if match else None
