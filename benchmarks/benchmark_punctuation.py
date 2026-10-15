"""Compare the pre-index and indexed punctuation lookup on reproducible synthetic text.

Run from the repository root:
    python benchmarks/benchmark_punctuation.py --size-mb 1 --url-count 25
For a large post-change-only measurement, use --optimized-only --size-mb 20 --url-count 500.
The legacy path intentionally retains the former O(characters * protected spans) lookup.
"""
from __future__ import annotations

import argparse
import time

from novel_epub.transforms import PunctuationTransformer


def legacy_transform(text: str) -> str:
    """Reference implementation of the pre-optimization punctuation loop."""
    transformer = PunctuationTransformer()
    protected = {
        match.span(): match.group(0)
        for match in transformer._URL_OR_EMAIL.finditer(text)
    }
    converted: list[str] = []
    chinese_context = False
    i = 0

    while i < len(text):
        protected_text = next(
            (value for (start, _), value in protected.items() if start == i),
            None,
        )
        if protected_text is not None:
            converted.append(protected_text)
            i += len(protected_text)
            continue

        char = text[i]
        direct = char.translate(transformer._DIRECT_MAP)
        if direct != char:
            converted.append(direct)
            i += 1
            continue

        if char == ".":
            end = i
            while end < len(text) and text[end] == ".":
                end += 1
            run_length = end - i
            if chinese_context and run_length >= 3:
                converted.append("……")
            elif chinese_context and run_length == 1:
                converted.append("。")
            else:
                converted.append(text[i:end])
            i = end
            continue

        if chinese_context and char in transformer._CONTEXT_MAP:
            converted.append(transformer._CONTEXT_MAP[char])
        else:
            converted.append(char)

        if transformer._is_meaningful(char):
            chinese_context = transformer._is_chinese(char)
        i += 1

    return "".join(converted)


def make_input(size_mb: int, url_count: int) -> str:
    target_chars = size_mb * 1024 * 1024
    urls = [f"https://example.com/chapter/{i}?q=a,b" for i in range(url_count)]
    separator = " 中文, "
    filler = "這是測試正文, 用來量測標點轉換效能。English, too! "
    fixed_chars = sum(map(len, urls)) + len(separator) * url_count
    remaining = target_chars - fixed_chars
    if remaining < 0:
        raise ValueError(
            f"{url_count} URLs and separators exceed the requested {target_chars:,} characters"
        )

    # Distribute the exact remaining character budget across the slots before,
    # between, and after URLs, so URL lengths are counted rather than deducted
    # from a budget that was already allocated to filler.
    slot_count = url_count + 1
    base, extra = divmod(remaining, slot_count)

    def filler_of_length(length: int) -> str:
        return (filler * (length // len(filler) + 1))[:length]

    chunks: list[str] = []
    for index, url in enumerate(urls):
        slot_length = base + (1 if index < extra else 0)
        chunks.extend((filler_of_length(slot_length), url, separator))
    chunks.append(filler_of_length(base + (1 if url_count < extra else 0)))
    result = "".join(chunks)
    assert len(result) == target_chars
    return result


def timed(label: str, function, text: str) -> tuple[str, float, str]:
    start = time.perf_counter()
    output = function(text)
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.3f}s ({len(text):,} chars)")
    return label, elapsed, output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size-mb", type=int, default=1)
    parser.add_argument("--url-count", type=int, default=25)
    parser.add_argument("--optimized-only", action="store_true")
    args = parser.parse_args()
    if args.size_mb < 1 or args.url_count < 0:
        parser.error("--size-mb must be >= 1 and --url-count must be >= 0")

    text = make_input(args.size_mb, args.url_count)
    optimized = timed(
        "indexed", lambda value: PunctuationTransformer().transform(value).text, text
    )
    if args.optimized_only:
        return
    baseline = timed("legacy", legacy_transform, text)
    if baseline[2] != optimized[2]:
        raise SystemExit("ERROR: legacy and indexed outputs differ")
    print(f"speedup: {baseline[1] / optimized[1]:.2f}x")
    print("output equivalence: OK")


if __name__ == "__main__":
    main()
