from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple
from .graphdb import GraphDBClient

# -------------------------
# Prefixes (unchanged)
# -------------------------
PREFIXES = """
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
"""

# -------------------------
# MAIN SPARQL (PRESERVED)
# Problems-only flexible query (unchanged)
# -------------------------
PROBLEMS_FROM_SECTIONS_FLEX = PREFIXES + r"""
SELECT ?paper ?paperLabel ?sectionLabel ?text
WHERE {
  {
    ?paper dcterms:title ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  } UNION {
    ?paper rdfs:label ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  }

  # section edge (name contains 'hasSection' or 'section')
  ?paper ?secPred ?section .
  FILTER(REGEX(LCASE(STR(?secPred)), "(hassection|section)"))

  # section label (optional)
  OPTIONAL { ?section rdfs:label ?sectionLabel }

  # content edge (name contains 'hasContent' or 'content')
  ?section ?contPred ?c .
  FILTER(REGEX(LCASE(STR(?contPred)), "(hascontent|content)"))

  # text from rdf:value OR rdfs:label OR dcterms:description
  {
    ?c rdf:value ?text
  } UNION {
    ?c rdfs:label ?text
  } UNION {
    ?c dcterms:description ?text
  }

  FILTER(REGEX(LCASE(STR(?text)), "(problem|challenge|issue|limitation|constraint)"))
}
LIMIT 1000
"""

CONTENTPART_FLEX = PREFIXES + r"""
SELECT ?paper ?paperLabel ?cpLabel ?text
WHERE {
  # match paper by title/label containing the term
  {
    ?paper dcterms:title ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  } UNION {
    ?paper rdfs:label ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  }

  # traverse to content part candidates
  {
    ?paper ?p1 ?cp .
    FILTER(REGEX(LCASE(STR(?p1)), "(contentpart|content_part|content|hascontent|section|hassection|ContentPart)"))
  } UNION {
    ?paper ?psec ?sec .
    FILTER(REGEX(LCASE(STR(?psec)), "(section|hassection)"))
    ?sec ?p2 ?cp .
    FILTER(REGEX(LCASE(STR(?p2)), "(contentpart|content_part|content|hascontent|ContentPart)"))
  }

  # ensure it's a ContentPart by class or IRI/name
  OPTIONAL { ?cp rdf:type ?cls . }
  FILTER(
       REGEX(LCASE(STR(?cp)), "(contentpart|content_part|ContentPart)")
    || REGEX(LCASE(STR(?cls)), "(contentpart)")
  )

  OPTIONAL { ?cp rdfs:label ?cpLabel }

  { ?cp rdf:value ?text } UNION { ?cp rdfs:label ?text } UNION { ?cp dcterms:description ?text }
}
LIMIT 200
"""


ABSTRACT_PURPOSE_FLEX = PREFIXES + r"""
SELECT ?paper ?paperLabel ?absLabel ?text
WHERE {
  # match paper by title/label containing the term
  {
    ?paper dcterms:title ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  } UNION {
    ?paper rdfs:label ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  }

  # link paper to an Abstract / Purpose node, directly or via a 'section'
  {
    ?paper ?p1 ?abs .
    FILTER(REGEX(LCASE(STR(?p1)), "(abstract|purpose|hasabstract|haspurpose|section|hassection)"))
  } UNION {
    ?paper ?psec ?sec .
    FILTER(REGEX(LCASE(STR(?psec)), "(section|hassection)"))
    ?sec ?p2 ?abs .
    FILTER(REGEX(LCASE(STR(?p2)), "(abstract|purpose|hasabstract|haspurpose|content|hascontent)"))
  }

  # ensure the node is abstract/purpose by class or by name
  OPTIONAL { ?abs rdf:type ?cls . }
  FILTER(
      REGEX(LCASE(STR(?abs)), "(abstract|purpose)")
   || REGEX(LCASE(STR(?cls)), "(abstract|purpose)")
  )

  OPTIONAL { ?abs rdfs:label ?absLabel }

  { ?abs rdf:value ?text } UNION { ?abs rdfs:label ?text } UNION { ?abs dcterms:description ?text }
}
LIMIT 1000
"""

GOAL_ACHIEVED_FLEX = PREFIXES + r"""
SELECT ?paper ?paperLabel ?goalLabel ?text
WHERE {
  # match paper by title/label containing the term
  {
    ?paper dcterms:title ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  } UNION {
    ?paper rdfs:label ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  }

  # traverse from paper to a goal/outcome node (direct or via section/content)
  {
    ?paper ?p1 ?g .
    FILTER(REGEX(LCASE(STR(?p1)), "(goal|hasgoal|result|outcome|hasresult|hasoutcome|section|hassection)"))
  } UNION {
    ?paper ?psec ?sec .
    FILTER(REGEX(LCASE(STR(?psec)), "(section|hassection)"))
    ?sec ?p2 ?g .
    FILTER(REGEX(LCASE(STR(?p2)), "(goal|hasgoal|result|outcome|content|hascontent)"))
  }

  # make sure node is GOAL_ACHIEVED (by class or name/IRI)
  OPTIONAL { ?g rdf:type ?cls . }
  FILTER(
       REGEX(LCASE(STR(?g)),   "(goal_achieved|goalachieved|goal achieved)")
    || REGEX(LCASE(STR(?cls)), "(goal_achieved|goalachieved|goal achieved)")
  )

  OPTIONAL { ?g rdfs:label ?goalLabel }
  { ?g rdf:value ?text } UNION { ?g rdfs:label ?text } UNION { ?g dcterms:description ?text }
}
LIMIT 200
"""

# -------------------------
# Tiny probe query (NEW, safe & cheap)
# Checks if a term appears in any paper title/label
# -------------------------
PROBE_TERM_SELECT = PREFIXES + r"""
SELECT ?paper
WHERE {
  {
    ?paper dcterms:title ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  }
  UNION
  {
    ?paper rdfs:label ?paperLabel .
    FILTER(CONTAINS(LCASE(STR(?paperLabel)), LCASE("%(kw)s")))
  }
}
LIMIT 1
"""

# -------------------------
# Stopwords (fixed commas; keep purely functional words)
# NOTE: Domain words (defect, warpage, delamination, thermal, etc.)
#       are intentionally NOT in stopwords so we don't throw away signal.
# -------------------------
STOPWORDS = {
    # common function words
    "the", "a", "an", "to", "of", "and", "or", "in", "on", "for", "with", "without", "by",
    "is", "are", "was", "were", "be", "been", "being", "that", "this", "these", "those",
    "what", "which", "who", "whom", "whose", "how", "why", "when", "where",
    # question/imperative filler
    "can", "could", "would", "should", "please", "kindly",
    "you", "your", "yours", "we", "us", "our", "ours", "i", "me", "my", "mine", "they", "them", "their", "theirs",
    "find", "show", "list", "several", "some", "any", "many", "much", "more", "most", "few", "lot",
    "need", "face", "related", "about", "around", "regarding", "regards", "regard",
    # generic boilerplate
    "paper", "papers", "problem", "problems", "issue", "issues", "challenge", "challenges",
}

# -------------------------
# Canonical phrases (fixed commas/typos; all lowercased)
# -------------------------
PHRASE_CANDIDATES = [
    "hybrid bonding", "bonding",  # (comma fixed)
    "advanced packaging",
    "direct to wafer", "direct-to-wafer", "d2w",
    "wafer to wafer", "wafer-to-wafer", "w2w",
    "die to wafer", "die-to-wafer",
    "foplp", "fan out", "fan-out", "plp",
    "plasma",
    "cow", "cowos",
    "warpage", "defect", "challenge", "problem", "thermal", "delamination", "cte", "thermal expansion",
]

# -------------------------
# Alias normalization for common variants/typos (NEW)
# -------------------------
ALIASES = {
    "advance packaging": "advanced packaging",
    "hybrid-bonding": "hybrid bonding",
    "die-to-wafer": "die to wafer",
    "wafer-to-wafer": "wafer to wafer",
    "direct-to-wafer": "direct to wafer",
    "d2w": "die to wafer",
    "w2w": "wafer to wafer",
    "cowos": "cowos",
    "co-wos": "cowos",
    "co wo s": "cowos",
}

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def _apply_aliases(q: str) -> str:
    qn = q
    for k, v in ALIASES.items():
        if k in qn:
            qn = qn.replace(k, v)
    return qn

# -------------------------
# Keyword extraction (manual)
# -------------------------
def extract_keywords(question: str, max_terms: int = 4) -> list[str]:
    """
    Manual extractor using PHRASE_CANDIDATES + singletons (minus STOPWORDS).
    Keeps order: phrases first, then strong singletons. Dedup + truncate.
    """
    q = _apply_aliases(_norm(question))

    # 1) phrase detection (2–3 word phrases we care about)
    found_phrases: List[str] = []
    for ph in PHRASE_CANDIDATES:
        if ph in q:
            found_phrases.append(ph)

    # 2) strong single-word terms (keep domain-y words)
    tokens = re.findall(r"[A-Za-z0-9_]+", q)
    singles: List[str] = []
    for t in tokens:
        if len(t) < 3:
            continue
        if t in STOPWORDS:
            continue
        singles.append(t)

    # 3) de-dup while preserving order
    out: List[str] = []
    seen = set()
    for item in found_phrases + singles:
        if item not in seen:
            out.append(item)
            seen.add(item)

    # 4) keep it compact
    return out[:max_terms] if out else singles[:max_terms]

# -------------------------
# Optional: probe whether a term exists in KG (fast SELECT 1)
# -------------------------
def _probe_term_exists(graph: GraphDBClient, term: str) -> bool:
    q = PROBE_TERM_SELECT % {"kw": term}
    try:
        res = graph.sparql_query(q)
        bindings = res.get("results", {}).get("bindings", [])
        return bool(bindings)
    except Exception:
        # fail-open to avoid blocking if probe errors
        return True

def _extract_keywords_probed(graph: GraphDBClient, question: str, max_terms: int = 4) -> List[str]:
    candidates = extract_keywords(question, max_terms=8)  # take a few more, then trim
    if not candidates:
        return []
    kept: List[str] = []
    for t in candidates:
        if _probe_term_exists(graph, t):
            kept.append(t)
        if len(kept) >= max_terms:
            break
    # if probe filtered everything, fall back to original (don’t return empty)
    return kept or candidates[:max_terms]

# -------------------------
# Run the preserved problems query for a single keyword
# -------------------------
def problems_by_keyword_flex(graph: GraphDBClient, kw: str) -> Tuple[List[Dict[str, str]], str]:
    sparql = PROBLEMS_FROM_SECTIONS_FLEX % {"kw": kw}
    res = graph.sparql_query(sparql)
    rows: List[Dict[str, str]] = []
    for b in res.get("results", {}).get("bindings", []):
        rows.append({
            "paper": b.get("paper", {}).get("value", ""),
            "paperLabel": b.get("paperLabel", {}).get("value", ""),
            "sectionLabel": b.get("sectionLabel", {}).get("value", ""),
            "text": b.get("text", {}).get("value", ""),
        })
    return rows, sparql


# -------------------------
# Abstract Purpose
# -------------------------
def abstract_purpose_by_term_flex(graph: GraphDBClient, term: str):
    q = ABSTRACT_PURPOSE_FLEX % {"kw": term}
    res = graph.sparql_query(q)
    rows = []
    for b in res.get("results", {}).get("bindings", []):
        rows.append({
            "paper": b.get("paper", {}).get("value", ""),
            "paperLabel": b.get("paperLabel", {}).get("value", ""),
            "absLabel": b.get("absLabel", {}).get("value", ""),
            "text": b.get("text", {}).get("value", ""),
        })
    return rows, q


# -------------------------
# Content Part
# -------------------------
def contentpart_by_term_flex(graph: GraphDBClient, term: str):
    q = CONTENTPART_FLEX % {"kw": term}
    res = graph.sparql_query(q)
    rows = []
    for b in res.get("results", {}).get("bindings", []):
        rows.append({
            "paper": b.get("paper", {}).get("value", ""),
            "paperLabel": b.get("paperLabel", {}).get("value", ""),
            "cpLabel": b.get("cpLabel", {}).get("value", ""),
            "text": b.get("text", {}).get("value", ""),
        })
    return rows, q

# -------------------------
# Goal Achieved
# -------------------------
def goal_achieved_by_term_flex(graph: GraphDBClient, term: str):
    q = GOAL_ACHIEVED_FLEX % {"kw": term}
    res = graph.sparql_query(q)
    rows = []
    for b in res.get("results", {}).get("bindings", []):
        rows.append({
            "paper": b.get("paper", {}).get("value", ""),
            "paperLabel": b.get("paperLabel", {}).get("value", ""),
            "goalLabel": b.get("goalLabel", {}).get("value", ""),
            "text": b.get("text", {}).get("value", ""),
        })
    return rows, q

# -------------------------
# Build the GraphDB context (manual path)
# probe=True uses the KG probe to avoid dead terms; set probe=False to disable
# -------------------------
# --- MODIFY the signature of build_graph_problem_context (add flag) ---
def build_graph_problem_context(
    graph: GraphDBClient,
    question: str,
    probe: bool = True,
    max_terms: int = 4,
    include_summaries: bool = True,
    include_content_parts: bool = True,
    include_goal_achieved: bool = True,   # NEW
) -> Tuple[str, Dict[str, Any]]:

    kws = _extract_keywords_probed(graph, question, max_terms=max_terms) if probe else extract_keywords(question, max_terms=max_terms)

    lines: List[str] = []

    # ✅ Make sure these keys exist up front
    debug: Dict[str, Any] = {
        "keywords": kws,
        "sparql": {},
        "rows_per_kw": {},
        "total_rows": 0,
        "probe_used": probe,
        "sparql_abs": {},
        "rows_abs_per_kw": {},
        "sparql_cp": {},
        "rows_cp_per_kw": {},
        "sparql_goal": {},           # NEW
        "rows_goal_per_kw": {},      # NEW
    }


    for kw in kws:
        # ✅ Always initialize these, even if include_summaries=False
        summary_rows: List[Dict[str, str]] = []
        sparql_abs: str = ""

        if include_summaries:
            try:
                summary_rows, sparql_abs = abstract_purpose_by_term_flex(graph, kw)
            except Exception as e:
                # keep it visible in debug instead of crashing
                sparql_abs = f"# ERROR: {type(e).__name__}: {e}"

        # ✅ Safe to write to the dict now
        debug["sparql_abs"][kw] = sparql_abs
        debug["rows_abs_per_kw"][kw] = len(summary_rows)

        # --- ContentPart (defensive) ---
        cp_rows: List[Dict[str, str]] = []
        sparql_cp: str = ""
        if include_content_parts:
            try:
                cp_rows, sparql_cp = contentpart_by_term_flex(graph, kw)
            except Exception as e:
                sparql_cp = f"# ERROR: {type(e).__name__}: {e}"

        debug["sparql_cp"][kw] = sparql_cp
        debug["rows_cp_per_kw"][kw] = len(cp_rows)

        # --- Goal_Achieved (defensive) ---
        goal_rows: List[Dict[str, str]] = []
        sparql_goal: str = ""
        if include_goal_achieved:
            try:
                goal_rows, sparql_goal = goal_achieved_by_term_flex(graph, kw)
            except Exception as e:
                sparql_goal = f"# ERROR: {type(e).__name__}: {e}"

        debug["sparql_goal"][kw] = sparql_goal
        debug["rows_goal_per_kw"][kw] = len(goal_rows)


        # -- existing problems query (unchanged) --
        rows, sparql = problems_by_keyword_flex(graph, kw)
        debug["sparql"][kw] = sparql
        debug["rows_per_kw"][kw] = len(rows)
        debug["total_rows"] += len(rows)

        if not rows and not summary_rows:
            continue

        lines.append(f"Keyword: {kw}")

        # groupers (unchanged)
        def _group(rr):
            g = {}
            for r in rr:
                key = r.get("paperLabel") or r.get("paper") or ""
                g.setdefault(key, []).append(r)
            return g

        g_sum = _group(summary_rows)
        g_prob = _group(rows)
        g_cp  = _group(cp_rows)
        g_goal = _group(goal_rows)

        all_papers = sorted(set(list(g_sum.keys()) + list(g_cp.keys()) + list(g_goal.keys()) + list(g_prob.keys())))

        for paper in all_papers:
            lines.append(f"- Paper: {paper}")

            if include_summaries and g_sum.get(paper):
                lines.append("  Summary:")
                seen = set()
                for r in g_sum[paper][:6]:
                    lab = r.get("absLabel") or ""
                    txt = re.sub(r"\s+", " ", (r.get("text") or "").strip())
                    if not txt or txt in seen: continue
                    seen.add(txt)
                    lines.append(f"    • {lab + ': ' if lab else ''}{txt}")

            if include_content_parts and g_cp.get(paper):
                lines.append("  Content:")
                seen = set()
                for r in g_cp[paper][:6]:
                    lab = r.get("cpLabel") or ""
                    txt = re.sub(r"\s+", " ", (r.get("text") or "").strip())
                    if not txt or txt in seen: continue
                    seen.add(txt)
                    lines.append(f"    • {lab + ': ' if lab else ''}{txt}")

            if include_goal_achieved and g_goal.get(paper):
                lines.append("  Solutions:")
                seen = set()
                for r in g_goal[paper][:8]:
                    lab = r.get("goalLabel") or ""
                    txt = re.sub(r"\s+", " ", (r.get("text") or "").strip())
                    if not txt or txt in seen: continue
                    seen.add(txt)
                    lines.append(f"    • {lab + ': ' if lab else ''}{txt}")

            if g_prob.get(paper):
                lines.append("  Problems:")
                seen = set()
                for r in g_prob[paper][:8]:
                    sec = r.get("sectionLabel") or ""
                    txt = re.sub(r"\s+", " ", (r.get("text") or "").strip())
                    if not txt or txt in seen: continue
                    seen.add(txt)
                    lines.append(f"    • {sec + ': ' if sec else ''}{txt}")

        lines.append("")

    return ("\n".join(lines).strip(), debug)


# -------------------------
# Prompt builder (unchanged)
# -------------------------
def build_prompt(question: str, vector_hits: Dict[str, Any], graph_context: str) -> str:
    ctx_parts = []
    docs = vector_hits.get("documents", [[]])
    metas = vector_hits.get("metadatas", [[]])
    for i, doc in enumerate(docs[0][:5] if docs else []):
        meta = metas[0][i] if metas and metas[0] and i < len(metas[0]) else {}
        src = meta.get("source") or meta.get("path") or ""
        ctx_parts.append(f"[Doc {i+1}] {src}\n{doc}")
    if graph_context:
        ctx_parts.append("[GraphDB]\n" + graph_context)

    context = "\n\n".join(ctx_parts) if ctx_parts else "(no context retrieved)"
    return f"""Role: 
 Act as a Hybrid Bonding Expert. 

2. Tasks 

Analyze the user query and extract the most accurate answers from the research paper context. 

Identify solutions relevant to the query and represent them as ontology triples. 

Extract all possible impacts described in the paper. For each impact: 

Show the effect/implication if the solution is implemented. 

Provide the source of the paper (title, section, or line reference). 

 

3.  Ontology Knowledge Representation 

Step 2: Solutions (S) – Ontology Triple Format 

(Subject – Predicate – Object) 

Sx : <Solution Subject> – <Predicate> – <Solution Object> 
 📖 Source: “<Paper Title>” (<Section/Heading/Subsection>) 

 

Step 3: Problem → Solution Mapping (M) 

Mx : Px – addressed → Sy 
 📖 Source: “<Paper Title>” (<Table/Figure/Section>) 

 

Step 4: Impacts (I) 

(Performance / Benefit impacts of the solutions) 

Ix : Sy → results in → <Impact Statement> 
  Source: “<Paper Title>” (<Section/Heading/Subsection>) 

 

4. Requirements 

Ensure all extracted knowledge is factually correct and aligned with the paper context. 

Represent impacts also as ontology triples, e.g.: 

Hybrid Bonding → Improves → Electrical Conductivity 

Solution Implementation → Leads to → Thermal Reliability Issues 

Use titles, section labels, or text lines as evidence. 

If information is found only in a title, inference is allowed, but the title must be cited as the source. 

Do not hallucinate. Only use the provided research paper context. 

Always present output in the sequence: Step 2 → Step 3 → Step 4. 

 
Question: {question}

Context:
{context}

Answer concisely with citations like [Doc i] or [GraphDB] when used.
"""
