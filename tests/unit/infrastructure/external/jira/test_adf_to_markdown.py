from src.app.infrastructure.external.jira.adf_to_markdown import adf_to_markdown
from src.app.infrastructure.external.jira.markdown_to_adf import markdown_to_adf


class TestAdfToMarkdown:
    def test_plain_paragraph(self):
        doc = {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Just a sentence."}]}]}
        assert adf_to_markdown(doc) == "Just a sentence."

    def test_bold_text(self):
        doc = markdown_to_adf("**As a** Backend Engineer")
        assert adf_to_markdown(doc) == "**As a** Backend Engineer"

    def test_heading(self):
        doc = markdown_to_adf("## Section Title")
        assert adf_to_markdown(doc) == "## Section Title"

    def test_bullet_list(self):
        doc = markdown_to_adf("- First item\n- Second item")
        assert adf_to_markdown(doc) == "- First item\n- Second item"

    def test_link(self):
        doc = markdown_to_adf("[Architecture Docs](../docs/architecture.md)")
        assert adf_to_markdown(doc) == "[Architecture Docs](../docs/architecture.md)"

    def test_multiple_blocks_separated_by_blank_line(self):
        doc = markdown_to_adf("First paragraph.\n\n- bullet one\n\nSecond paragraph.")
        assert adf_to_markdown(doc) == "First paragraph.\n\n- bullet one\n\nSecond paragraph."

    def test_checklist_glyph_prefix_preserved(self):
        doc = markdown_to_adf("- [ ] Todo item\n- [x] Done item")
        result = adf_to_markdown(doc)
        assert "☐ Todo item" in result
        assert "☑ Done item" in result

    def test_empty_doc_returns_empty_string(self):
        assert adf_to_markdown({"type": "doc", "version": 1, "content": []}) == ""

    def test_plain_string_passthrough(self):
        assert adf_to_markdown("already plain text") == "already plain text"

    def test_none_returns_empty_string(self):
        assert adf_to_markdown(None) == ""

    def test_unrecognized_node_type_falls_back_without_crashing(self):
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "blockquote",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Quoted text."}]}],
                }
            ],
        }
        assert adf_to_markdown(doc) == "Quoted text."
