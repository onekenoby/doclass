# graphdb/graph_builder.py

import re
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

# Locate and load the .env file in the project root
env_path = Path(__file__).resolve().parents[1] / ".env"
print(f"[DEBUG] Loading .env from {env_path}")
load_dotenv(env_path, override=True)

# Read and sanitize Neo4j connection details
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

#uri = "bolt://127.0.0.1:7690"
#user = "neo4j"
#password = "onekenoby"



print(f"[DEBUG] Neo4j → URI={uri!r}, USER={user!r}, PASS_LOADED={bool(password)}")

# Initialize the Neo4j driver
try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
except Exception as e:
    print(f"❌ Failed to initialize Neo4j driver: {e}")
    driver = None


def preprocess_script(cypher_script: str) -> str:
    """
    Clean the raw Cypher script:
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
    Execute each MERGE/CREATE statement after preprocessing.
    If the driver is not initialized, skip execution gracefully.
    """
    if driver is None:
        print("❌ Cannot execute queries: Neo4j driver not initialized.")
        return

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
            except exceptions.AuthError:
                print("❌ Authorization error: please check NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD.")
                return
            except exceptions.CypherSyntaxError as e:
                print(f"⚠️ Syntax error in Cypher:\n{stmt}\n→ {e.message}")
            except exceptions.Neo4jError as e:
                print(f"⚠️ Neo4j execution error:\n{stmt}\n→ {e.message}")


def close_driver():
    """
    Close the Neo4j driver connection.
    """
    if driver:
        driver.close()
