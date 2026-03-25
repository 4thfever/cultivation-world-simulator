"""Tests for MiniMax LLM provider preset integration."""

import json
import os
import pytest


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(BASE_DIR, "web", "src", "locales")
PANEL_PATH = os.path.join(
    BASE_DIR, "web", "src", "components", "game", "panels", "system", "LLMConfigPanel.vue"
)


class TestMiniMaxPresetLocales:
    """Verify MiniMax preset keys exist in all locale files."""

    LOCALES = ["en-US", "zh-CN", "zh-TW", "vi-VN"]

    def _load_llm_json(self, locale: str) -> dict:
        path = os.path.join(LOCALES_DIR, locale, "llm.json")
        assert os.path.exists(path), f"{locale}/llm.json not found"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.mark.parametrize("locale", LOCALES)
    def test_minimax_preset_key_exists(self, locale: str):
        """Each locale must have a 'minimax' key under presets."""
        data = self._load_llm_json(locale)
        presets = data.get("presets", {})
        assert "minimax" in presets, (
            f"{locale}/llm.json is missing 'presets.minimax' key"
        )
        assert presets["minimax"], f"{locale}/llm.json has empty 'presets.minimax' value"

    @pytest.mark.parametrize("locale", LOCALES)
    def test_minimax_help_link_exists(self, locale: str):
        """Each locale must have a 'minimax' key under help_links."""
        data = self._load_llm_json(locale)
        help_links = data.get("help_links", {})
        assert "minimax" in help_links, (
            f"{locale}/llm.json is missing 'help_links.minimax' key"
        )
        assert help_links["minimax"], (
            f"{locale}/llm.json has empty 'help_links.minimax' value"
        )

    def test_minimax_preset_values_consistent(self):
        """MiniMax preset name should be 'MiniMax' in all locales (brand name)."""
        for locale in self.LOCALES:
            data = self._load_llm_json(locale)
            preset_name = data["presets"]["minimax"]
            assert "MiniMax" in preset_name or "minimax" in preset_name.lower(), (
                f"{locale} MiniMax preset name '{preset_name}' doesn't contain 'MiniMax'"
            )


class TestMiniMaxPresetPanel:
    """Verify MiniMax preset configuration in LLMConfigPanel.vue."""

    def _read_panel(self) -> str:
        assert os.path.exists(PANEL_PATH), "LLMConfigPanel.vue not found"
        with open(PANEL_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def test_minimax_preset_defined(self):
        """LLMConfigPanel.vue must define a MiniMax preset."""
        content = self._read_panel()
        assert "llm.presets.minimax" in content, (
            "LLMConfigPanel.vue is missing MiniMax preset definition"
        )

    def test_minimax_base_url(self):
        """MiniMax preset must use the correct API base URL."""
        content = self._read_panel()
        assert "https://api.minimax.io/v1" in content, (
            "LLMConfigPanel.vue is missing MiniMax base URL"
        )

    def test_minimax_model_names(self):
        """MiniMax preset must specify correct model names."""
        content = self._read_panel()
        assert "MiniMax-M2.7" in content, (
            "LLMConfigPanel.vue is missing MiniMax-M2.7 model name"
        )
        assert "MiniMax-M2.5-highspeed" in content, (
            "LLMConfigPanel.vue is missing MiniMax-M2.5-highspeed fast model name"
        )

    def test_minimax_help_link_in_panel(self):
        """LLMConfigPanel.vue must include MiniMax platform help link."""
        content = self._read_panel()
        assert "platform.minimaxi.com" in content, (
            "LLMConfigPanel.vue is missing MiniMax platform help link"
        )
        assert "llm.help_links.minimax" in content, (
            "LLMConfigPanel.vue is missing MiniMax help link i18n key"
        )


class TestMiniMaxReadmeMention:
    """Verify MiniMax is mentioned in README files."""

    README_FILES = [
        os.path.join(BASE_DIR, "README.md"),
        os.path.join(BASE_DIR, "docs", "readme", "EN_README.md"),
        os.path.join(BASE_DIR, "docs", "readme", "ZH-TW_README.md"),
        os.path.join(BASE_DIR, "docs", "readme", "VI-VN_README.md"),
    ]

    @pytest.mark.parametrize("readme_path", README_FILES)
    def test_minimax_mentioned_in_readme(self, readme_path: str):
        """Each README file should mention MiniMax."""
        assert os.path.exists(readme_path), f"{readme_path} not found"
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "MiniMax" in content, (
            f"{os.path.basename(readme_path)} does not mention MiniMax"
        )


class TestMiniMaxApiIntegration:
    """Integration tests for MiniMax API connectivity (require MINIMAX_API_KEY)."""

    @pytest.fixture
    def api_key(self):
        key = os.environ.get("MINIMAX_API_KEY")
        if not key:
            pytest.skip("MINIMAX_API_KEY not set")
        return key

    def test_minimax_chat_completions(self, api_key):
        """Verify MiniMax API responds to a chat completion request."""
        import urllib.request
        import urllib.error

        url = "https://api.minimax.io/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        data = json.dumps({
            "model": "MiniMax-M2.5-highspeed",
            "messages": [{"role": "user", "content": "Reply with OK"}],
            "max_tokens": 10,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            assert "choices" in result, "MiniMax API response missing 'choices'"
            assert len(result["choices"]) > 0, "MiniMax API returned empty choices"
            content = result["choices"][0]["message"]["content"]
            assert content, "MiniMax API returned empty content"
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            pytest.fail(f"MiniMax API returned HTTP {e.code}: {body}")
