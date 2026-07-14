from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ThirdPartyLicensesTests(unittest.TestCase):
    def test_optional_requirements_are_documented(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
        license_text = (PROJECT_ROOT / "THIRD_PARTY_LICENSES.txt").read_text(
            encoding="utf-8"
        )

        direct_packages = []
        for line in requirements.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            direct_packages.append(re.split(r"[<>=!~]", line, maxsplit=1)[0].strip().lower())

        self.assertEqual(direct_packages, ["anthropic"])
        for package in direct_packages:
            self.assertIn(package, license_text.lower())

        self.assertIn("Direct optional dependency", license_text)
        self.assertIn("MIT", license_text)
        self.assertIn("OSV result on 2026-07-14", license_text)
        self.assertNotIn("C:\\Users\\", license_text)

    def test_readme_and_changelog_link_license_inventory(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("THIRD_PARTY_LICENSES.txt", readme)
        self.assertIn("THIRD_PARTY_LICENSES.txt", changelog)


if __name__ == "__main__":
    unittest.main()
