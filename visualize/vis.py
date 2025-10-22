import re
from collections import defaultdict

# ============================================================
# FILE PATHS - CONFIGURE THESE
# ============================================================
INPUT_SQL_FILE = r'database-qldh\database.sql'
OUTPUT_PLANTUML_FILE = r'database-qldh\visualize\diagram.puml'

# ============================================================
# PARSER
# ============================================================

def parse_sql_schema(sql_content):
    tables = {}
    relationships = []

    sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)

    table_pattern = r'CREATE TABLE\s+(\w+)\s*\((.*?)\);'
    for match in re.finditer(table_pattern, sql_content, re.DOTALL | re.IGNORECASE):
        table_name = match.group(1)
        table_body = match.group(2)
        columns = []
        lines, current_line, paren_depth = [], "", 0

        for char in table_body:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                lines.append(current_line.strip())
                current_line = ""
                continue
            current_line += char
        if current_line.strip():
            lines.append(current_line.strip())

        for line in lines:
            if not line:
                continue
            fk = re.search(r'FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+(\w+)\s*\((\w+)\)', line, re.IGNORECASE)
            if fk:
                relationships.append((match.group(1), fk.group(1), fk.group(2), fk.group(3)))
                continue
            m = re.match(r'(\w+)\s+', line)
            if m:
                columns.append(m.group(1))
        tables[table_name] = columns

    return tables, relationships


# ============================================================
# LEVEL DETERMINATION
# ============================================================

def determine_table_levels(tables, relationships):
    """Compute topological levels with parents (referenced tables) on top"""
    dependents = defaultdict(set)
    for from_table, _, to_table, _ in relationships:
        if from_table != to_table:
            dependents[to_table].add(from_table)  # reverse dependency

    levels = {}
    processed = set()

    roots = [t for t in tables if t not in dependents or not dependents[t]]
    for t in roots:
        levels[t] = 0
        processed.add(t)

    changed = True
    while changed and len(processed) < len(tables):
        changed = False
        for t in tables:
            if t in processed:
                continue
            parents = [p for p, _, c, _ in relationships if c == t]
            if parents and all(p in levels for p in parents):
                levels[t] = max(levels[p] for p in parents) + 1
                processed.add(t)
                changed = True

    for t in tables:
        if t not in levels:
            levels[t] = 0
    return levels


# ============================================================
# PLANTUML GENERATOR
# ============================================================

def generate_plantuml(tables, relationships):
    lines = [
        "@startuml",
        "!theme plain",
        "top to bottom direction",
        "skinparam classAttributeIconSize 0",
        "skinparam linetype ortho",
        "",
        "skinparam class {",
        "  BackgroundColor LightBlue",
        "  BorderColor Blue",
        "}",
        ""
    ]

    levels = determine_table_levels(tables, relationships)
    tables_by_level = defaultdict(list)
    for t, lvl in levels.items():
        tables_by_level[lvl].append(t)

    for lvl in sorted(tables_by_level.keys()):
        lines.append(f"' Level {lvl} tables")
        for t in sorted(tables_by_level[lvl]):
            lines.append(f"class {t} {{")
            for c in tables[t]:
                lines.append(f"  {c}")
            lines.append("}")
        lines.append("")

    lines.append("' Relationships")
    seen = set()
    for f, _, t, _ in relationships:
        if f != t and (f, t) not in seen:
            lines.append(f"{t} --> {f}")  # arrow from parent(top) → child(bottom)
            seen.add((f, t))

    lines.append("@enduml")
    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        with open(INPUT_SQL_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
        tables, rels = parse_sql_schema(sql)
        puml = generate_plantuml(tables, rels)
        with open(OUTPUT_PLANTUML_FILE, 'w', encoding='utf-8') as f:
            f.write(puml)
        print("✓ Root tables now appear at the top.")
    except Exception as e:
        print("✗ Error:", e)
