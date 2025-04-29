# neo4j/graph_builder.py
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def execute_cypher_queries(cypher_script):
    queries = cypher_script.split(";")
    with driver.session() as session:
        for query in queries:
            cleaned = query.strip()
            if cleaned:
                session.run(cleaned)
    driver.close()
