from neo4j import GraphDatabase
import os, textwrap, collections, itertools
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
)

# ---------- helper queries ----------
LABELS_QUERY = "CALL db.labels() YIELD label RETURN label ORDER BY label"
RTYPE_QUERY  = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType"
COUNT_NODES  = "MATCH (n) RETURN count(n) AS c"
COUNT_RELS   = "MATCH ()-[r]->() RETURN count(r) AS c"

# sample 1 000 entity names to guess theme
SAMPLE_NAMES = """
MATCH (e:Entity)
WHERE e.name IS NOT NULL
WITH e.name AS n
LIMIT 1000
RETURN n
"""

HUBS_QUERY = """
MATCH (n)-[r]-()
WITH n, count(r) AS deg
ORDER BY deg DESC
LIMIT 5
RETURN coalesce(n.name,n.filename, n.index) AS name, labels(n)[0] AS lbl, deg
"""


def fetch(tx, q):
    return [r[0] for r in tx.run(q)]


def describe_graph():
    with driver.session() as s:
        node_cnt = s.run(COUNT_NODES).single()["c"]
        rel_cnt  = s.run(COUNT_RELS).single()["c"]
        labels   = fetch(s, LABELS_QUERY)
        rtypes   = fetch(s, RTYPE_QUERY)
        hubs     = s.run(HUBS_QUERY).data()
        sample   = fetch(s, SAMPLE_NAMES)

    # ---------- semantic topic guess ----------
    words = [
        w.lower()
        for name in sample
        for w in name.split()
        if 2 < len(w) < 30                      # drop tiny tokens
           and w[0].isalpha()                   # skip numbers / punctuation
    ]
    common = collections.Counter(words).most_common(5)
    topic_phrase = ", ".join(w for w, _ in common) if common else "various subjects"

    # ---------- narrative -------------
    label_str = ", ".join(f"`{l}`" for l in labels) or "no labels"
    rel_str   = ", ".join(f"`:{t}`" for t in rtypes) or "no relationship types"

    story = []
    story += [
        f"Your knowledge-graph currently contains **{node_cnt:,} nodes** and "
        f"**{rel_cnt:,} relationships**.",
        f"It uses the labels {label_str} and the relationship types {rel_str}.",
        f"From a quick semantic scan, the graph seems to revolve around **{topic_phrase}**."
    ]

    if hubs:
        hub_txt = "; ".join(f"{h['name']} ({h['lbl']}, degree {h['deg']})" for h in hubs)
        story.append(f"The most connected objects are {hub_txt}.")

    print("\n" + textwrap.fill(" ".join(story), width=92) + "\n")


if __name__ == "__main__":
    describe_graph()
    driver.close()
