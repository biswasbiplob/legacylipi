"""Font size analysis and normalization for translated documents."""

from legacylipi.core.models import TextBlock


class FontSizeAnalyzer:
    """Analyze font sizes across document and normalize for consistency.

    This class analyzes all text blocks in a document, infers font sizes from
    bounding box dimensions (for OCR where no font info is available), clusters
    them into categories (heading/body/caption), and provides normalized output
    sizes to preserve visual hierarchy while maintaining consistency.
    """

    CATEGORY_HEADING = "heading"
    CATEGORY_BODY = "body"
    CATEGORY_CAPTION = "caption"

    # Normalized output sizes for each category
    # For now, use SINGLE consistent size for all text to ensure uniformity
    # TODO: Implement smarter heading detection using text length, position, etc.
    UNIFORM_SIZE = 11.0  # Single consistent size for all text
    OUTPUT_SIZES = {
        CATEGORY_HEADING: 11.0,  # Same as body for consistency
        CATEGORY_BODY: 11.0,
        CATEGORY_CAPTION: 11.0,  # Same as body for consistency
    }

    # Percentile thresholds for categorization
    HEADING_PERCENTILE = 85  # Top 15% are headings
    CAPTION_PERCENTILE = 15  # Bottom 15% are captions

    def __init__(self):
        """Initialize the analyzer."""
        self._block_sizes: dict[int, float] = {}  # block id -> inferred size
        self._block_categories: dict[int, str] = {}  # block id -> category
        self._analyzed = False

    def analyze_blocks(self, blocks: list[TextBlock]) -> None:
        """Analyze all blocks to determine font categories.

        Args:
            blocks: List of TextBlock objects to analyze.
        """
        if not blocks:
            self._analyzed = True
            return

        # Collect inferred sizes for all blocks with positions
        sizes = []
        for block in blocks:
            if not block.position:
                continue

            # Infer size from bounding box height
            # For OCR blocks, font_size defaults to 12.0, so we use bbox height
            bbox_height = block.position.height
            # If font_size is not default (12.0), use it; otherwise infer from bbox
            if block.font_size != 12.0:
                inferred_size = block.font_size
            else:
                # Approximate: bbox height ≈ font size + leading (factor ~0.85)
                inferred_size = bbox_height * 0.85

            # Store for this block
            block_id = id(block)
            self._block_sizes[block_id] = inferred_size
            sizes.append(inferred_size)

        if not sizes:
            self._analyzed = True
            return

        # Calculate percentiles for clustering
        sizes_sorted = sorted(sizes)
        n = len(sizes_sorted)

        # Handle edge cases
        if n == 1:
            # Single block - treat as body
            for block_id in self._block_sizes:
                self._block_categories[block_id] = self.CATEGORY_BODY
            self._analyzed = True
            return

        # Calculate percentile thresholds
        heading_idx = int(n * self.HEADING_PERCENTILE / 100)
        caption_idx = int(n * self.CAPTION_PERCENTILE / 100)

        heading_threshold = sizes_sorted[min(heading_idx, n - 1)]
        caption_threshold = sizes_sorted[max(caption_idx, 0)]

        # Check if there's meaningful size variation
        size_range = sizes_sorted[-1] - sizes_sorted[0]
        if size_range < 3.0:  # Less than 3pt difference - treat all as body
            for block_id in self._block_sizes:
                self._block_categories[block_id] = self.CATEGORY_BODY
            self._analyzed = True
            return

        # Categorize each block
        for block_id, size in self._block_sizes.items():
            if size >= heading_threshold:
                self._block_categories[block_id] = self.CATEGORY_HEADING
            elif size <= caption_threshold:
                self._block_categories[block_id] = self.CATEGORY_CAPTION
            else:
                self._block_categories[block_id] = self.CATEGORY_BODY

        self._analyzed = True

    def get_normalized_font_size(self, block: TextBlock) -> float:
        """Get the normalized font size for a block.

        Args:
            block: The TextBlock to get font size for.

        Returns:
            Normalized font size based on category.
        """
        block_id = id(block)
        category = self._block_categories.get(block_id, self.CATEGORY_BODY)
        return self.OUTPUT_SIZES.get(category, self.OUTPUT_SIZES[self.CATEGORY_BODY])

    def get_category(self, block: TextBlock) -> str:
        """Get the font category for a block.

        Args:
            block: The TextBlock to get category for.

        Returns:
            Category string (heading, body, or caption).
        """
        block_id = id(block)
        return self._block_categories.get(block_id, self.CATEGORY_BODY)

    def set_block_categories(self, blocks: list[TextBlock]) -> None:
        """Set font_category field on all analyzed blocks.

        Args:
            blocks: List of TextBlock objects to update.
        """
        for block in blocks:
            block_id = id(block)
            if block_id in self._block_categories:
                block.font_category = self._block_categories[block_id]
