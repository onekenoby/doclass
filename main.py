# main.py
from preprocess.text_extractor import extract_text_from_file
from gemini.gemini_client    import generate_cypher_from_text
from graphdb.graph_builder   import execute_cypher_queries
from graph_report            import descrivi_grafo   # ← NEW

def main():
    filepath = "samples/sample.pdf"
    text     = extract_text_from_file(filepath)

    cypher   = generate_cypher_from_text(text)
    execute_cypher_queries(cypher)

    # ---- print human‑readable interpretation ----
    descrivi_grafo()          # <– this prints the narrative to stdout

if __name__ == "__main__":
    main()
