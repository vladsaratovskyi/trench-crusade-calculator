from django.shortcuts import render

from .forms import AttackInputForm, KeywordForm, UnitProfileForm
from .logic import (
    AttackInput,
    DEFAULT_INJURY_BANDS,
    attack_outcome_probabilities,
    success_probability,
)
from .models import Keyword, UnitProfile


def _as_percent(value: float) -> str:
    return f"{value*100:.2f}%"


def _ensure_profiles_exist():
    if not UnitProfile.objects.exists():
        UnitProfile.objects.create(name="Baseline", ranged_dice_mod=0, melee_dice_mod=0, armor=0)


def _build_results(cleaned_data):
    attacker = cleaned_data["attacker_profile"]
    defender = cleaned_data["defender_profile"]
    attack_type = cleaned_data["attack_type"]

    atk_kw_totals = attacker.keyword_totals()
    def_kw_totals = defender.keyword_totals()

    base_hit_dice_mod = (
        attacker.ranged_dice_mod if attack_type == "ranged" else attacker.melee_dice_mod
    )
    keyword_hit_mod = (
        atk_kw_totals["ranged_dice_mod"] if attack_type == "ranged" else atk_kw_totals["melee_dice_mod"]
    )

    hit_dice_mod = base_hit_dice_mod + keyword_hit_mod + cleaned_data["extra_hit_dice_mod"]

    base_armor = defender.armor
    keyword_armor_mod = def_kw_totals["armor_mod"]
    target_armor = base_armor + keyword_armor_mod + cleaned_data["extra_target_armor"]

    attack = AttackInput(
        hit_target_number=cleaned_data["hit_target_number"],
        hit_dice_mod=hit_dice_mod,
        hit_roll_mod=cleaned_data["hit_roll_mod"],
        weapon_is_critical=cleaned_data.get("weapon_is_critical", False),
        injury_bands=DEFAULT_INJURY_BANDS,
        injury_dice_mod=cleaned_data["injury_dice_mod"],
        injury_roll_mod=cleaned_data["injury_roll_mod"],
        target_armor=target_armor,
    )

    outcome = attack_outcome_probabilities(attack)
    hit_prob = success_probability(
        target_number=cleaned_data["hit_target_number"],
        dice_mod=hit_dice_mod,
        roll_mod=cleaned_data["hit_roll_mod"],
    )
    any_injury = 1.0 - outcome.get("Miss", 0.0)

    return {
        "attacker": attacker,
        "defender": defender,
        "attack_type": attack_type,
        "base_hit_dice_mod": base_hit_dice_mod,
        "keyword_hit_mod": keyword_hit_mod,
        "hit_dice_mod": hit_dice_mod,
        "extra_hit_dice_mod": cleaned_data["extra_hit_dice_mod"],
        "hit_target_number": cleaned_data["hit_target_number"],
        "hit_roll_mod": cleaned_data["hit_roll_mod"],
        "base_armor": base_armor,
        "target_armor": target_armor,
        "extra_target_armor": cleaned_data["extra_target_armor"],
        "keyword_armor_mod": keyword_armor_mod,
        "injury_dice_mod": cleaned_data["injury_dice_mod"],
        "injury_roll_mod": cleaned_data["injury_roll_mod"],
        "attacker_keywords": list(attacker.keywords.all()),
        "defender_keywords": list(defender.keywords.all()),
        "hit_probability": _as_percent(hit_prob),
        "miss_probability": _as_percent(outcome.get("Miss", 0.0)),
        "any_injury_probability": _as_percent(any_injury),
        "bands": [
            {
                "label": band.label,
                "percent": _as_percent(outcome.get(band.label, 0.0)),
                "raw": outcome.get(band.label, 0.0),
            }
            for band in DEFAULT_INJURY_BANDS
        ],
    }


def _default_payload():
    form = AttackInputForm(prefix="attack")
    # If no profiles exist yet, bail
    if not UnitProfile.objects.exists():
        return None

    payload = {}
    for name, field in form.fields.items():
        if name in {"attacker_profile", "defender_profile"}:
            payload[name] = form.initial.get(name) or field.queryset.first()
        else:
            payload[name] = form.initial.get(name, field.initial)
    return payload


def calculator_view(request):
    _ensure_profiles_exist()
    results = None
    attack_form = AttackInputForm(request.POST or None, prefix="attack")
    profile_form = UnitProfileForm(prefix="profile")
    keyword_form = KeywordForm(prefix="keyword")

    if request.method == "POST":
        if "create_profile" in request.POST:
            profile_form = UnitProfileForm(request.POST, prefix="profile")
            attack_form = AttackInputForm(prefix="attack")
            if profile_form.is_valid():
                new_profile = profile_form.save()
                profile_form = UnitProfileForm(prefix="profile")
                attack_form = AttackInputForm(
                    prefix="attack",
                    initial={
                        "attacker_profile": new_profile,
                        "defender_profile": new_profile,
                    },
                )
        elif "create_keyword" in request.POST:
            keyword_form = KeywordForm(request.POST, prefix="keyword")
            attack_form = AttackInputForm(prefix="attack")
            profile_form = UnitProfileForm(prefix="profile")
            if keyword_form.is_valid():
                keyword_form.save()
                keyword_form = KeywordForm(prefix="keyword")
                # Refresh profile form choices to include new keyword
                profile_form = UnitProfileForm(prefix="profile")
        else:
            if attack_form.is_bound and attack_form.is_valid():
                results = _build_results(attack_form.cleaned_data)
            profile_form = UnitProfileForm(prefix="profile")
            keyword_form = KeywordForm(prefix="keyword")

    if results is None:
        defaults = _default_payload()
        if defaults:
            results = _build_results(defaults)
            if not attack_form.is_bound:
                attack_form.initial.update(
                    {
                        "attacker_profile": defaults["attacker_profile"],
                        "defender_profile": defaults["defender_profile"],
                    }
                )

    return render(
        request,
        "calculator/index.html",
        {
            "attack_form": attack_form,
            "profile_form": profile_form,
            "keyword_form": keyword_form,
            "results": results,
        },
    )
