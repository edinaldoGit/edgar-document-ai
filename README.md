# EDGAR

**Fine-Grained Multimodal RAG for Document Intelligence**

EDGAR is a multimodal Retrieval-Augmented Generation architecture designed
to process complex documents at fine-grained component level, combining
document layout analysis, localized text extraction, visual understanding,
semantic retrieval, and evidence-grounded answer generation.

## Status

🚧 Under active development.

## Architecture

The system is organized around two main processing flows:

- Offline document ingestion and indexing.
- Online retrieval and evidence-grounded generation.

## Project Structure

```text
src/            Core EDGAR architecture
apps/           Client applications
experiments/    Experimental evaluation and baselines
tests/          Automated tests
data/           Research and evaluation datasets
storage/        Runtime-generated document artifacts
scripts/        Utility and execution scripts
configs/        System and experiment configurations
docs/           Architecture and development documentation
