# Python Utilities & Automation Scripts

A collection of personal Python scripts designed for audio file management, metadata inspection, and media organization.

## Structure

- `audio-tools/`
  - `cover_cropper.py`: Automatically inspects audio files, extracts embedded artwork, and crops it into a 1:1 square ratio while offering dry-run and backup protections.
  - `song_counter.py`: Recursively counts audio tracks across directories while filtering out non-audio files (e.g., `.lrc` lyrics).
  - `directory_counter.py`: Provides detailed directory breakdowns, counting both audio files and nested folders.

## Prerequisites

Ensure you have Python installed. Install the required external packages using:

```bash
pip install music-tag Pillow

