# BeagleMind QA Dataset

This file defines the unified QA format used by BeagleMind for RAG and future SFT.

## Record schema

Each QA record has:

- `question` (string): User-style question.
- `answer` (string): Final answer text.
- `source_type` (string): One of `"docs"`, `"forum"`, `"discord"`, `"other"`.
- `source_id` (string): Identifier for where the answer came from (URL, file path, message ID, etc.).
- `tags` (list of strings): Optional labels like board type, topic, difficulty.

## Storage format

- Format: **JSON Lines** (one JSON object per line).
- Default path: `data/qa_dataset_docs.jsonl`.

## Building the dataset

From the project root:

