# Privacy and publication boundaries

This repository is designed around a private, local dataset. No real phone content is required or included.

## Never commit

- personal images or documents;
- SQLite inventories created from real collections;
- content hashes or manifests containing real paths;
- face embeddings, cluster identifiers or thumbnails;
- MTP logs, device names or hardware identifiers;
- downloaded model weights;
- backups, quarantine folders or classified output.

The included `.gitignore` blocks the expected locations, but it is not a substitute for reviewing staged files before every commit.

## Local model processing

OpenCLIP, OpenCV and optional classifiers run locally. Some packages download model weights from their upstream hosts during first use. The input files are not uploaded by this project.

## Biometric and sensitive-content features

The private case study used local recurring-person signals and a private-content filter. The public reference implementation omits biometric persistence and personal category labels. Anyone extending it must obtain appropriate consent, minimize retained data and comply with applicable law.

## Safe examples

Use synthetic documents, public-domain images or generated fixtures. Replace personal categories with neutral examples such as `pets`, `travel`, `screenshots` and `other`.
