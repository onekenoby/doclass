# graphdb/graph_builder.py
import re
from neo4j import GraphDatabase, exceptions
import os
from dotenv import load_dotenv
from gemini.gemini_client import generate_narrative_from_cypher

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def preprocess_script(cypher_script: str) -> str:
    """
    Clean the raw script:
    - Remove stray 'cypher' markers
    - Collapse newlines inside string literals
    - Escape internal double quotes
    """
    script = re.sub(r'(?m)^\s*cypher\s*$', '', cypher_script)
    def escape_literal(match):
        content = match.group(1).replace('\n', ' ').replace('"', '\\"')
        return f'"{content}"'
    return re.sub(
        r'"([^"\n]*(?:\n[^"\n]*)*)"',
        escape_literal,
        script,
        flags=re.DOTALL
    )

def execute_cypher_queries(cypher_script: str):
    """
    Execute each MERGE/CREATE after preprocessing, respecting
    the hierarchy: Documento -> Paragrafo -> Contenuto.
    """
    script = preprocess_script(cypher_script)
    statements = []
    for part in script.split(';'):
        for line in part.splitlines():
            stmt = line.strip()
            if stmt:
                statements.append(stmt)

    with driver.session() as session:
        for stmt in statements:
            try:
                session.run(stmt)
            except exceptions.CypherSyntaxError as e:
                print(f"⚠️ Syntax error:\n{stmt}\n→ {e.message}")
            except exceptions.Neo4jError as e:
                print(f"⚠️ Execution error:\n{stmt}\n→ {e.message}")
    driver.close()

def get_graph_schema():
    """
    Retrieve the current graph schema:
      • node labels, with their indexes & constraints
      • relationship types
    Returns:
      node_schemas: [{ name, indexes: [...], constraints: [...] }, …]
      rel_schemas:  [{ name }, …]
    """
    with driver.session() as session:
        labels = [r["label"] for r in session.run("CALL db.labels()")]
        rel_types = [r["relationshipType"] for r in session.run("CALL db.relationshipTypes()")]
        idx_records = list(session.run("SHOW INDEXES"))
        cons_records = list(session.run("SHOW CONSTRAINTS"))

    node_schemas = []
    for label in labels:
        idx_props = []
        for rec in idx_records:
            types = rec.get("labelsOrTypes") or []
            if label in types:
                props = rec.get("properties") or []
                idx_props.extend(props)
        cons_desc = []
        for rec in cons_records:
            types = rec.get("labelsOrTypes") or []
            if label in types:
                name = rec.get("name") or rec.get("type")
                cons_desc.append(name)
        node_schemas.append({
            "name": label,
            "indexes": sorted(set(idx_props)),
            "constraints": cons_desc
        })

    rel_schemas = [{"name": r} for r in sorted(set(rel_types))]
    return node_schemas, rel_schemas

def interpret_graph(cypher_script: str):
    """
    1) Print the Italian narrative.
    2) Fetch & print the full schema structure.
    """
    narrative_it = generate_narrative_from_cypher(cypher_script)
    print("\n=== Interpretazione Semantica del Grafo ===\n")
    print(narrative_it)

    node_schemas, rel_schemas = get_graph_schema()
    print("\n=== Schema del Grafo ===\n")
    print(node_schemas)
    print(rel_schemas)
