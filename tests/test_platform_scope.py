from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PlatformScopeTests(unittest.TestCase):
    def test_readme_declares_mobile_and_web_as_non_targets(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Desktop-/CLI-Projekt", readme)
        self.assertIn("Web/PWA, Android und iOS sind keine Portierungsziele", readme)
        self.assertIn("eigenes Produkt", readme)

    def test_no_mobile_or_web_scaffold_is_present(self):
        forbidden_dirs = [
            "web_companion",
            "flutter_port",
            "android",
            "ios",
        ]

        for dirname in forbidden_dirs:
            with self.subTest(dirname=dirname):
                self.assertFalse((PROJECT_ROOT / dirname).exists())


if __name__ == "__main__":
    unittest.main()
