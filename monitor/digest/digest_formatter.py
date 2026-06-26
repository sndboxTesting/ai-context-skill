#!/usr/bin/env python3
"""Format scored monitor items as a Markdown morning brief."""

from datetime import datetime


def format_brief(scored_items: list[tuple[dict, float]], date_str: str, total_fetched: int) -> str:
    lines = [
        f"# Morning Brief — {date_str}",
        f"",
        f"*Generated {datetime.now().strftime('%H:%M')} · {len(scored_items)} relevant items from {total_fetched} fetched*",
        f"",
    ]

    if not scored_items:
        lines.append("*No items above relevance threshold today.*")
        return "\n".join(lines)

    # Group by source type
    groups: dict[str, list[tuple[dict, float]]] = {}
    for item, score in scored_items:
        src = item.get("source", "other")
        key = "Research (Arxiv)" if src == "arxiv" else \
              "GitHub" if src.startswith("github:") else \
              "News & Blogs"
        groups.setdefault(key, []).append((item, score))

    for group_name in ("News & Blogs", "GitHub", "Research (Arxiv)"):
        items = groups.get(group_name, [])
        if not items:
            continue
        lines.append(f"## {group_name}")
        lines.append("")
        for item, score in items:
            title = item.get("title", "(no title)")
            url = item.get("url", "")
            summary = item.get("summary", "").strip()
            pub = item.get("published", "")[:10]
            rel_pct = int(score * 100)

            link = f"[{title}]({url})" if url else title
            lines.append(f"### {link}")
            if pub:
                lines.append(f"*{pub} · relevance {rel_pct}%*")
            if summary:
                lines.append(f"")
                lines.append(summary)
            if group_name == "Research (Arxiv)":
                authors = item.get("authors", [])
                if authors:
                    lines.append(f"")
                    lines.append(f"*Authors: {', '.join(authors)}*")
            lines.append("")

    return "\n".join(lines)
