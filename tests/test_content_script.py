import pytest

from poe.content.script import ScriptGenerationError, build_caption, build_script
from poe.models import PriceInfo, ProductCandidate


def make_candidate(marketing_analysis=None, category="pet / higiene"):
    return ProductCandidate(
        name="Bebedouro Automático Para Gatos",
        category=category,
        seed_keyword="",
        price=PriceInfo(min_brl=55.0),
        marketing_analysis=marketing_analysis,
    )


MA = {
    "hooks": ["Hook 1", "Hook 2", "Hook 3", "Hook 4"],
    "first_second": "Corte rápido mostrando o problema.",
    "objections": [{"objection": "Faz barulho?", "response": "Não, é silencioso."}],
}


def test_build_script_requires_marketing_analysis():
    cand = make_candidate(marketing_analysis=None)
    with pytest.raises(ScriptGenerationError):
        build_script(cand)


def test_build_script_requires_hooks():
    cand = make_candidate(marketing_analysis={"objections": []})
    with pytest.raises(ScriptGenerationError):
        build_script(cand)


def test_build_script_creates_hook_fact_objection_cta_scenes():
    cand = make_candidate(marketing_analysis=MA)
    script = build_script(cand)

    kinds = [s.kind for s in script.scenes]
    assert kinds[0] == "hook"
    assert "fact" in kinds
    assert "objection" in kinds
    assert kinds[-1] == "cta"


def test_build_script_hook_uses_first_second_as_narration():
    cand = make_candidate(marketing_analysis=MA)
    script = build_script(cand)

    hook_scene = script.scenes[0]
    assert hook_scene.on_screen_text == "Hook 1"
    assert hook_scene.narration_text == "Corte rápido mostrando o problema."


def test_build_script_without_objections_skips_objection_scene():
    ma = {"hooks": ["Hook 1"], "objections": []}
    cand = make_candidate(marketing_analysis=ma)
    script = build_script(cand)

    kinds = [s.kind for s in script.scenes]
    assert "objection" not in kinds
    assert kinds == ["hook", "cta"]


def test_search_query_matches_pet_category():
    cand = make_candidate(marketing_analysis=MA, category="pet / higiene e bem-estar animal")
    script = build_script(cand)
    assert "cat" in script.scenes[0].search_query


def test_search_query_falls_back_to_default_for_unknown_category():
    cand = make_candidate(marketing_analysis=MA, category="categoria-nunca-vista")
    script = build_script(cand)
    assert script.scenes[0].search_query  # não vazio, usa o default


def test_build_caption_includes_first_hook():
    cand = make_candidate(marketing_analysis=MA)
    caption = build_caption(cand)
    assert "Hook 1" in caption
