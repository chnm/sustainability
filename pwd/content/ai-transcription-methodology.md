---
title: "Transcription Methodology Using Generative AI"
slug: transcription-methodology
type: page
---

## Overview

The *Papers of the War Department* collection contains over 42,000 documents, many of which are handwritten correspondence and records from the late 18th century. Since 2011, volunteer transcribers have contributed human transcriptions of these documents. To supplement this effort and expand access to documents that have not yet been transcribed by hand, the project has developed an AI-assisted transcription pipeline using generative AI.

AI transcriptions are presented alongside human transcriptions in a tabbed interface on each document page. Where a human transcription exists, it remains the primary text. AI transcriptions are clearly labeled and should be understood as machine-generated readings that may contain errors, particularly with difficult handwriting, damaged documents, or unusual letterforms.

Code and documentation about the transcription process are available [in our Github repository](https://github.com/chnm/sustainability/tree/feat/main/pwd/_transcription).

## Model and Approach

AI transcriptions are generated using [Anthropic's Claude](https://www.anthropic.com/claude), a large language model with vision capabilities for reading handwritten text. The default model used is **Claude Sonnet 4.6** (`claude-sonnet-4-6`), though the pipeline supports other Claude model variants.

Each document's page images are sent to the model via the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI along with a detailed system prompt that instructs the model to act as an expert paleographer specializing in 18th-century American handwritten documents. The model processes the images and returns a plain-text transcription.

## Transcription Guidelines

The AI transcription prompt follows the same editorial standards used by human transcribers on this project:

- **Faithful reproduction**: The text is transcribed exactly as it appears, preserving original spelling, punctuation, and capitalization, even when unconventional by modern standards.
- **No modernization**: Spelling is not corrected or standardized. Punctuation and capitalization follow the original document.
- **Marginalia and notations**: Postal notations, administrative notes, and other marginalia are recorded in brackets. Documents marked "Private", "Confidential", or "Copy" by the author are noted in brackets.
- **Document markings**: Strikethroughs are indicated as `[strikethrough: text]`, underlined text as `[underline: text]`, and superscript characters use `<sup>` tags (e.g., May 19<sup>th</sup>, 1793). Illustrations, seals, and symbols that cannot be reproduced are noted in brackets (e.g., `[seal]`).
- **Illegible text**: Words that cannot be deciphered are marked `[undecipherable]`. Partial readings are noted as `[undecipherable: probable reading]`. The model is instructed never to guess or fabricate text.
- **Multi-page documents**: Pages are transcribed in order as a continuous document without page markers.
- **Scope**: Only the primary document in each record is transcribed. Some documents are part of letter books with many letters per page; only the letter or document that is the primary subject of the record is included.
- **Output**: The model returns only the transcription text, with no commentary, analysis, or metadata.

## Technical Pipeline

The transcription pipeline works as follows:

1. **Image manifest**: A build script scans all document frontmatter to produce a manifest (`images.tsv`) mapping each document's identifier to its page image filename(s). Only documents with associated images are included.
2. **Image retrieval**: For each document, original-resolution page images are downloaded from the project's object storage to a temporary directory.
3. **Transcription**: Images are passed to the Claude Code CLI (`claude -p`) along with the paleography system prompt. The CLI handles the API submission, including reading the image files.
4. **Output storage**: Transcriptions are saved to a structured JSON file (`transcriptions.json`), keyed by each document's identifier. This file is read by Hugo at build time and displayed in the AI transcription tab.
5. **Batch processing**: Documents are processed sequentially. A progress cache tracks completed documents so that interrupted runs can be resumed. Documents exceeding a configurable page limit (default: 50 pages) are skipped and handled separately. Temporary image files are cleaned up automatically after each document.

## Limitations

AI transcription of 18th-century handwriting is an imperfect process. Users should be aware of the following limitations:

- **Handwriting variability**: The quality of AI transcriptions varies with the legibility of the original handwriting. Documents written in clear, consistent hands produce better results than those with irregular or hurried script.
- **Damaged or faded documents**: Ink fading, water damage, tears, and other physical deterioration reduce transcription accuracy.
- **Abbreviations and conventions**: Period-specific abbreviations, contractions (e.g., the "thorn" character for "the"), and letterforms may be misread.
- **Context and proper nouns**: The model may misread unfamiliar place names, personal names, or specialized terminology from the period.
- **Not a substitute for scholarly editing**: AI transcriptions have not been reviewed or corrected by human editors. They are provided as a reading aid, not as a definitive scholarly text.

## Use and Citation

AI transcriptions are provided to improve access to the collection and to support research, teaching, and public engagement. When citing an AI-generated transcription, users should note that it is a machine-generated text. We recommend the following citation format:

> [Document title], Papers of the War Department, 1784–1800. AI transcription generated by Claude (Anthropic). [URL]. Accessed [date].
