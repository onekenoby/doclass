from preprocess.text_extractor import extract_text_from_file
from gemini.gemini_client import generate_cypher_from_text
from graphdb.graph_builder import execute_cypher_queries, interpret_graph

def main():
    filepath = "samples/sample.pdf"  # or .docx
    text = extract_text_from_file(filepath)
    cypher = generate_cypher_from_text(text)
    execute_cypher_queries(cypher)
    interpret_graph(cypher)

if __name__ == "__main__":
    main()
    