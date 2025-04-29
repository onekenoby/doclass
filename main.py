
# main.py
from preprocess.text_extractor import extract_text_from_file
from gemini.gemini_client import generate_cypher_from_text
from neo4j.graph_builder import execute_cypher_queries


def main():
    filepath = "samples/sample.pdf"  # or .docx
    text = extract_text_from_file(filepath)
    cypher = generate_cypher_from_text(text)
    execute_cypher_queries(cypher)


if __name__ == "__main__":
    main()

