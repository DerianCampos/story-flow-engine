from typing import Any


def adf_to_markdown(doc: Any) -> str:
    """
    Converts an Atlassian Document Format (ADF) document back into markdown
    text, the read-direction counterpart to markdown_to_adf(). Handles the
    node shapes markdown_to_adf() itself produces (paragraph, heading,
    bulletList/listItem, text with strong/link marks); falls back to
    recursing into unrecognized nodes' content rather than raising, since
    Jira's own rich-text editor can introduce node types outside that set.

    Args:
        doc: The ADF document (dict), or an already-plain string.

    Returns:
        Readable markdown text.
    """
    if not isinstance(doc, dict):
        return doc if isinstance(doc, str) else ("" if doc is None else str(doc))

    blocks = [_render_block(node) for node in doc.get("content", [])]
    return "\n\n".join(block for block in blocks if block)


def _render_block(node: dict) -> str:
    node_type = node.get("type")

    if node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        return "#" * level + " " + _render_inline(node.get("content", []))

    if node_type == "paragraph":
        return _render_inline(node.get("content", []))

    if node_type in ("bulletList", "taskList"):
        lines = []
        for item in node.get("content", []):
            item_text = " ".join(
                _render_block(child) for child in item.get("content", [])
            )
            lines.append(f"- {item_text}")
        return "\n".join(lines)

    # Unrecognized node type: recurse into any nested content rather than
    # dropping it silently or raising on content this tool didn't produce.
    nested = node.get("content")
    if not nested:
        return ""
    if all(child.get("type") == "text" for child in nested):
        return _render_inline(nested)
    return "\n\n".join(_render_block(child) for child in nested)


def _render_inline(nodes: list) -> str:
    parts = []
    for node in nodes:
        if node.get("type") != "text":
            continue
        text = node.get("text", "")
        for mark in node.get("marks", []):
            mark_type = mark.get("type")
            if mark_type == "strong":
                text = f"**{text}**"
            elif mark_type == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)
