from src.app.infrastructure.external.jira.markdown_to_adf import markdown_to_adf


class TestMarkdownToAdf:
    def test_plain_paragraph(self):
        doc = markdown_to_adf("Just a sentence.")

        assert doc == {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Just a sentence."}]}
            ],
        }

    def test_bold_text_gets_strong_mark(self):
        doc = markdown_to_adf("**As a** Backend Engineer")

        paragraph = doc["content"][0]
        assert paragraph["type"] == "paragraph"
        assert paragraph["content"][0] == {
            "type": "text",
            "text": "As a",
            "marks": [{"type": "strong"}],
        }
        assert paragraph["content"][1] == {"type": "text", "text": " Backend Engineer"}

    def test_heading(self):
        doc = markdown_to_adf("## Section Title")

        assert doc["content"][0]["type"] == "heading"
        assert doc["content"][0]["attrs"] == {"level": 2}
        assert doc["content"][0]["content"][0]["text"] == "Section Title"

    def test_bullet_list(self):
        doc = markdown_to_adf("- First item\n- Second item")

        node = doc["content"][0]
        assert node["type"] == "bulletList"
        assert len(node["content"]) == 2
        assert node["content"][0]["type"] == "listItem"
        assert node["content"][0]["content"][0]["type"] == "paragraph"
        assert node["content"][0]["content"][0]["content"][0]["text"] == "First item"

    def test_checklist_becomes_bullet_list_with_checkbox_glyph(self):
        # Jira's issue create/edit API rejects ADF "taskList" nodes for the
        # description field, so checklists fall back to a plain bulletList.
        doc = markdown_to_adf("- [ ] Todo item\n- [x] Done item")

        node = doc["content"][0]
        assert node["type"] == "bulletList"
        assert node["content"][0]["type"] == "listItem"

        todo_text_nodes = node["content"][0]["content"][0]["content"]
        assert todo_text_nodes[0] == {"type": "text", "text": "☐ "}
        assert todo_text_nodes[1] == {"type": "text", "text": "Todo item"}

        done_text_nodes = node["content"][1]["content"][0]["content"]
        assert done_text_nodes[0] == {"type": "text", "text": "☑ "}
        assert done_text_nodes[1] == {"type": "text", "text": "Done item"}

    def test_checklist_and_plain_bullets_share_one_list(self):
        doc = markdown_to_adf("- Plain bullet\n- [ ] Checklist item")

        assert len(doc["content"]) == 1
        assert doc["content"][0]["type"] == "bulletList"
        assert len(doc["content"][0]["content"]) == 2

    def test_link_gets_link_mark(self):
        doc = markdown_to_adf("[Architecture Docs](../docs/architecture.md)")

        text_node = doc["content"][0]["content"][0]
        assert text_node["text"] == "Architecture Docs"
        assert text_node["marks"] == [{"type": "link", "attrs": {"href": "../docs/architecture.md"}}]

    def test_blank_lines_separate_blocks(self):
        doc = markdown_to_adf("First paragraph.\n\n- bullet one\n\nSecond paragraph.")

        types = [node["type"] for node in doc["content"]]
        assert types == ["paragraph", "bulletList", "paragraph"]

    def test_empty_text_returns_empty_paragraph(self):
        doc = markdown_to_adf("")

        assert doc == {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": []}]}
