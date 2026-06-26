"""Insurance agent demo package.

Four OpenAI-backed agents spanning the governance risk spectrum:

  #1 Policy Q&A Assistant        — LOW       (read-only, internal KB)
  #3 Customer Service Email      — MEDIUM    (PII, drafts only)
  #5 Underwriting Risk Advisor   — HIGH      (PII + actuarial, recommends)
  #6 Claims Auto-Adjudication    — CRITICAL  (PHI, autonomous decision)
"""
