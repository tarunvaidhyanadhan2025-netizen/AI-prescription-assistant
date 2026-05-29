"""
Retrieval Prompt Templates
LangChain prompt templates for RAG query reformulation
and context synthesis from retrieved documents.
"""

# ── Query Reformulation Prompt ─────────────────────────────────────────────
QUERY_REFORMULATION_PROMPT = """
You are a medical information retrieval expert.
Given a medicine name or clinical query, generate 3 alternative search queries
that would retrieve the most relevant clinical information.

Original query: {query}

Return ONLY JSON:
{{
  "queries": [
    "<reformulated query 1>",
    "<reformulated query 2>",
    "<reformulated query 3>"
  ]
}}
"""

# ── Context Synthesis Prompt ───────────────────────────────────────────────
CONTEXT_SYNTHESIS_PROMPT = """
You are a clinical pharmacist synthesising information from multiple sources.
Combine the retrieved documents into a coherent clinical summary.

Medicine: {medicine_name}
Retrieved Documents:
---
{documents}
---

Synthesise a clinical summary covering:
- Primary indication
- Mechanism
- Key safety concerns
- Important patient counselling points

Return ONLY JSON:
{{
  "summary": "<clinical summary>",
  "key_facts": ["<fact 1>", "<fact 2>", ...],
  "safety_highlights": ["<highlight 1>", ...],
  "counselling_points": ["<point 1>", ...]
}}
"""

# ── Relevance Scoring Prompt ───────────────────────────────────────────────
RELEVANCE_SCORING_PROMPT = """
Rate the relevance of this document to the query.

Query: {query}
Document: {document}

Return ONLY JSON:
{{
  "relevance_score": <0.0 to 1.0>,
  "relevant_sections": ["<relevant excerpt 1>", ...],
  "reasoning": "<brief reason>"
}}
"""

# ── Fallback Knowledge Prompt ──────────────────────────────────────────────
FALLBACK_KNOWLEDGE_PROMPT = """
No documents were retrieved from the database for: {medicine_name}

As a clinical pharmacist, provide your best knowledge about this medicine.
Note: This is based on general pharmacological knowledge, not a specific database entry.

Return ONLY JSON:
{{
  "found": <true/false — false if medicine is unknown>,
  "name": "{medicine_name}",
  "drug_class": "<class if known>",
  "use_case": "<indication if known>",
  "key_safety_points": ["<point 1>", ...],
  "confidence": "<high|medium|low>",
  "disclaimer": "Based on general pharmacological knowledge. Verify with current prescribing information."
}}
"""
