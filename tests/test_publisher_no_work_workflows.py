"""Publisher workflows must treat publication_claim exit 3 as clean NO-WORK only."""
from pathlib import Path

WORKFLOWS=(
 ".github/workflows/instagram-publish.yml",
 ".github/workflows/facebook-publish.yml",
 ".github/workflows/instagram-reels.yml",
 ".github/workflows/instagram-stories.yml",
 ".github/workflows/instagram-carousel.yml",
 ".github/workflows/facebook-carousel.yml",
)

def test_no_work_is_clean_but_real_errors_stay_red():
    for path in WORKFLOWS:
        text=Path(path).read_text(encoding="utf-8")
        assert "id: claim" in text,path
        assert 'if [ "$rc" -eq 3 ]; then' in text,path
        assert 'echo "has_claim=false" >> "$GITHUB_OUTPUT"' in text,path
        assert 'exit "$rc"' in text,path
        assert "if: steps.claim.outputs.has_claim == 'true'" in text,path
        # The claim wrapper alone may map rc=3 to success. It must not use a
        # blanket suppression that would hide genuine publication_claim errors.
        assert "publication_claim.py" in text and "|| true" not in "\n".join(
            line for line in text.splitlines() if "publication_claim.py" in line
        ),path
