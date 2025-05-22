import re

def extract_sql_from_response(response_text):
    match = re.search(r"```sql\n(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
