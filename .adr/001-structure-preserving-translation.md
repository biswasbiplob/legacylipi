# ADR 001: Structure-Preserving Translation

## Status
Accepted

## Context
The original translation implementation combined all text from a PDF into a single string, translated it, and then flowed the translated text onto pages. This approach loses the original document structure and layout.

Users want translations that preserve the document layout, similar to how Google Translate handles document translation - where each text region is translated separately and placed at its original position.

## Decision
Implement block-level translation with position preservation:

1. **Store translation at block level**: Add `translated_text` field to `TextBlock` dataclass to store per-block translations
2. **Translate blocks individually**: Add `translate_blocks_async()` method that translates each block separately with concurrent API calls (max 3) and rate limiting
3. **Font scaling**: Scale font size down (by 10% increments, min 5pt) to fit translated text within original bounding box dimensions
4. **Position preservation**: Render translated text at original (x0, y0) coordinates using bounding box data

## Consequences

### Positive
- Document layout is preserved in translation
- Users get output that matches their expectations from tools like Google Translate
- Block-level translation allows for better progress tracking in UI
- Font scaling ensures text fits even when translations are longer

### Negative
- More API calls required (one per block vs one per document)
- Longer processing time due to rate limiting between requests
- Font scaling may result in smaller text for blocks where translation is significantly longer
- Only works with PDF output format (text/markdown still use flowing mode)

### Neutral
- Requires position data from OCR or PDF parsing (falls back to flowing mode if unavailable)
- Concurrent translation with semaphore balances speed vs rate limiting

## Alternatives Considered

1. **Page-level translation**: Translate each page separately. Rejected because it still loses intra-page positioning.
2. **Table-based layout**: Use table structure to maintain positions. Rejected as overly complex for this use case.
3. **Image overlay**: Keep original as image, overlay translated text. Rejected as it would lose text selectability.
