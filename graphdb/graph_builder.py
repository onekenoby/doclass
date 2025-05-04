# graphdb/graph_builder.py
from neo4j import GraphDatabase
import os, re
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    database=os.getenv("NEO4J_DB", "neo4j"),
)

# --- NUOVA funzione ------------------------------------------------
def execute_cypher_queries(cypher_script: str):
    """
    Invia i comandi Cypher generati da Gemini.
    • rimuove eventuali alias (var:) ripetuti
    • scarta righe vuote o la sola parola «cypher»
    """
    alias_strip = re.compile(r"\(\s*\w+\s*:")      # (alias:
    statements  = [ln.strip() for ln in cypher_script.split("\n")]

    with driver.session() as session:
        for stmt in statements:
            if not stmt or stmt.lower() == "cypher":
                continue                          # ← salta righe indesiderate
            cleaned = alias_strip.sub("(", stmt)  # ← toglie alias
            try:
                print(f"🔁 Executing:\n{cleaned}")
                session.run(cleaned)
            except Exception as e:
                print(f"⚠️  Query failed:\n{cleaned}\nError: {e}")

    driver.close()

# -------------------------------------------------------------------
