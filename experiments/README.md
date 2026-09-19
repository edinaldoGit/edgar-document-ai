# EDGAR Experiments

This directory contains the experimental evaluation framework for EDGAR.

## Structure

- `datasets/`: definitions of documents and evaluation questions.
- `runs/`: generated outputs from individual experiment executions.
- `reports/`: summarized experimental results.
- `scripts/`: automation scripts used to execute and evaluate experiments.

## Experimental Goals

The experiments evaluate EDGAR's ability to process complex documents using multimodal representations.

Main evaluation dimensions:

- document ingestion;
- component extraction;
- indexing;
- retrieval quality;
- multimodal contribution.

Each experiment run should generate reproducible artifacts containing:

- configuration;
- execution metadata;
- generated metrics;
- analysis results.
