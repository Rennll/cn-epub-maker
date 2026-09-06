from __future__ import annotations

from argparse import Namespace
from typing import Any


_CLI_FIELDS = (
    "input",
    "output",
    "title",
    "author",
    "lang",
    "cover",
    "encoding",
    "opencc",
    "opencc_profile",
    "punctuation",
    "full_source",
    "paragraph_mode",
)


def namespace_to_inputs(args: Namespace) -> dict[str, Any]:
    """Convert argparse output into resolver input data.

    The adapter is the only layer that knows the CLI Namespace shape. Optional
    CLI values are kept as ``None`` when unspecified so the resolver can apply
    config-file values and application defaults.
    """
    return {
        "source": args.input,
        "destination": args.output,
        "title": args.title,
        "author": args.author,
        "lang": args.lang,
        "cover": args.cover,
        "encoding": args.encoding,
        "opencc": args.opencc,
        "opencc_profile": args.opencc_profile,
        "punctuation": args.punctuation,
        "full_source": args.full_source,
        "paragraph_mode": args.paragraph_mode,
    }
