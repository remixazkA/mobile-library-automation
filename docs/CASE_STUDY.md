# Case study: from phone migration to an auditable local pipeline

## Roles and authorship

The project owner supplied the problem context, desired outcome, examples and priorities, reviewed the deliverables, requested adjustments and asked for minimal model-token consumption. Codex translated that direction into technical requirements, designed the architecture and safety mechanisms, and generated the code, tests and technical documentation.

The project owner did not design or write the source code. The outcome is presented as an AI-directed automation project: the owner's contribution was problem framing, direction, review, requests for adjustments and publication, not software-engineering or machine-learning authorship.

## Context

A recent phone replacement turned a routine migration into a data-quality problem. Useful personal photos were buried under screenshots, random downloads, memes and images accumulated through messaging groups. A second collection contained years of academic and reference documents with inconsistent names and little usable folder structure.

The project treated both collections as one information-management problem: acquire safely, build a durable inventory, extract evidence, propose classifications, apply only reviewed changes and verify the final state.

## Constraints

The resulting technical design followed these constraints. They describe the solution implemented by Codex and are not attributed to the project owner as personally designed technical requirements.

- The phone exposed storage through Windows MTP rather than a normal filesystem.
- Personal photos and documents could not be sent to a cloud classification service.
- A false deletion was much more expensive than retaining an unwanted file.
- The workflow needed to survive interruption and support recalibration without starting over.
- Results had to be explainable through a stored category and reason.

## Pipeline

### 1. Safe acquisition

PowerShell and `Shell.Application` copied selected MTP roots into local staging. Copy and inventory were intentionally separate because an MTP object tree does not provide ordinary filesystem guarantees.

### 2. Incremental inventory

SQLite stored relative path, size, modification time, SHA-256, image dimensions, quality measures, semantic scores, classification and reason. Unchanged items were skipped on later runs.

### 3. Image analysis

The private production pipeline combined:

- OpenCLIP zero-shot prototypes for configurable categories;
- basic quality and exposure measures;
- exact duplicates through SHA-256;
- optional local sensitive-content detection;
- YuNet/SFace embeddings grouped with DBSCAN for recurring-person signals.

Model output was treated as evidence, not truth. Deterministic safety rules had precedence and every result retained its reason.

### 4. Document analysis

The document pipeline extracted titles or opening text from PDF, DOCX, XLSX and plain text, normalized Unicode and generated a collision-safe rename plan. Documents were grouped by subject and period while preserving their original bytes and extensions.

### 5. Review, transfer and verification

Every material stage produced a plan or manifest before file operations. The selected photo set was copied to a new phone folder and checked by file count, category and total bytes. Exact-duplicate handling used SHA-256 only; perceptually similar images were never deleted automatically.

## Measured outcome

- 17,569 staged files yielded 14,664 supported images.
- 954 images were selected for five useful categories.
- 42 exact duplicate copies were isolated.
- 315 documents were classified and 179 received meaningful or normalized names.
- Eight audio support files were identified and excluded from the document destination.
- The transferred photo set was verified at 954 files and 894,715,013 bytes.

## What went wrong

The hardest part was not model inference; it was reliable MTP automation. Cancelled child processes could retain MTP handles, virtual paths could not be passed to ordinary Win32 file APIs and dialog-driven deletion depended on Windows language and timing. These failures led to three design decisions:

1. keep destructive MTP logic outside the public reusable core;
2. use one worker process with explicit state and closed manifests;
3. verify the device after every transfer or cleanup operation.

## Evaluation limits

The run proves complete processing and operational verification, not perfect classification accuracy. OpenCLIP values are not calibrated probabilities, and the personal categories do not have a public labelled ground-truth set. A production evaluation would sample each predicted class, label it manually and report precision, recall and a confusion matrix.

## Why the repository is sanitized

Publishing the original dataset, SQLite database or manifests would expose private filenames, document subjects, content hashes, device identifiers and biometric embeddings. This repository therefore publishes reusable engineering patterns, configuration examples and synthetic tests rather than the private artefacts.
