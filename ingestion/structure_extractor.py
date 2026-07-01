# ============================================================
# structure_extractor.py
# ------------------------------------------------------------
# Purpose: Take the raw text we extracted from a PDF page and
# ask an LLM to understand its STRUCTURE — not just read it, but
# figure out what's a heading, what's a bullet list, what's a
# comparison (like "X vs Y"), what's a sequence/timeline, what's
# a definition, and now also what's a REFERENCE/citation (so we
# can filter these out of search results later — bibliography
# entries are usually not useful search results for a student).
#
# Why this matters: this structured understanding is the shared
# foundation for TWO features later:
#   1. Better search — we can chunk text by actual logical
#      sections instead of blindly cutting every N characters,
#      AND we can exclude low-value sections (like references)
#      from search results
#   2. Restructuring — we can turn "comparison" sections into
#      tables, "sequence" sections into flow diagrams, etc.
# ============================================================

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


STRUCTURE_EXTRACTION_PROMPT = """You are analyzing text extracted from a study document (like exam prep notes or an academic paper).

Read the text below and break it into structured sections. For each section, identify:
- "type": one of ["heading", "paragraph", "bullet_list", "comparison", "sequence", "definition", "reference"]
- "title": a short title for this section (if it has one, otherwise null)
- "content": the actual text content of this section

Rules:
- "comparison" = content that contrasts two or more things (e.g. "X vs Y", "difference between A and B")
- "sequence" = content describing ordered steps, phases, or a timeline
- "definition" = content that defines a specific term or concept
- "bullet_list" = a list of related points with no inherent order
- "heading" = a section title/header with no body content of its own
- "paragraph" = general explanatory text that doesn't fit the above categories
- "reference" = a bibliography citation, footnote, or works-cited entry — typically starts with author names, contains "arXiv preprint", a DOI, journal/conference name, or appears in a numbered reference list at the end of a document

Respond ONLY with valid JSON in this exact format, no other text:
{
  "sections": [
    {"type": "...", "title": "...", "content": "..."},
    ...
  ]
}

Here is the text to analyze:
"""


def extract_structure(page_text, model="gpt-4o-mini"):
    """
    Sends one page's text to the LLM and gets back a structured
    breakdown of its content.

    Args:
        page_text (str): raw text extracted from a PDF page
        model (str): which OpenAI model to use

    Returns:
        dict: parsed JSON with a "sections" list, or empty sections
              list if something went wrong
    """
    if len(page_text.strip()) < 20:
        return {"sections": []}

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": STRUCTURE_EXTRACTION_PROMPT + page_text
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        raw_output = response.choices[0].message.content
        return json.loads(raw_output)

    except Exception as e:
        print(f"[structure_extractor] Failed to process page: {e}")
        return {"sections": []}


if __name__ == "__main__":
    sample_text = """
    References

    [1] Ralle: A framework for developing and evaluating retrieval-augmented 
    large language models, arXiv preprint arXiv:2308.10633, 2023.

    Abstract. Large Language Models (LLMs) showcase impressive capabilities 
    in various natural language processing tasks.
    """

    result = extract_structure(sample_text)
    print(json.dumps(result, indent=2))