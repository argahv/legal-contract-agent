#!/usr/bin/env python3
"""Stub — Legal Agent does not train models in-repo. Point people at the right next step."""

print(
    """
Fine-tuning (LoRA / QLoRA / DPO) is intentionally out of scope for this repository.

Recommended order for Legal Agent:
  1) Hybrid retrieval + rerank + evals (see tests/eval/)
  2) Human approval labels exported to JSONL for supervised fine-tuning
  3) External training job (Axolotl, Unsloth, TRL) with consent-scoped data
  4) Serve adapters via vLLM or merge weights; route in Settings.openai_model

Do not fine-tune before RAG + rule_engine + eval gates plateau.
"""
)
