from django.shortcuts import get_object_or_404, redirect, render

from .forms import AttackInputForm, KeywordForm, UnitProfileForm, WeaponForm
from .logic import (
    AttackInput,
    DEFAULT_INJURY_BANDS,
    attack_outcome_probabilities,
    success_probability,
)
from .models import Keyword, UnitProfile, Weapon


def _as_percent(value: float) -> str:
    return f"{value*100:.2f}%"


def _ensure_profiles_exist():
    if not UnitProfile.objects.exists():
        UnitProfile.objects.create(name="Baseline", ranged_dice_mod=0, melee_dice_mod=0, armor=0)


def _build_results(cleaned_data):
    attacker = cleaned_data["attacker_profile"]
    weapon = cleaned_data.get("weapon") or attacker.weapons.first()
    defender = cleaned_data["defender_profile"]
    attack_type = weapon.range_type if weapon else cleaned_data["attack_type"]

    atk_kw_totals = attacker.keyword_totals()
    weapon_kw_totals = weapon.keyword_totals() if weapon else {"ranged_dice_mod": 0, "melee_dice_mod": 0, "armor_mod": 0}
    def_kw_totals = defender.keyword_totals()

    base_hit_dice_mod = (
        attacker.ranged_dice_mod if attack_type == "ranged" else attacker.melee_dice_mod
    )
    keyword_hit_mod = (
        atk_kw_totals["ranged_dice_mod"] if attack_type == "ranged" else atk_kw_totals["melee_dice_mod"]
    )
    weapon_hit_mod = (
        weapon_kw_totals["ranged_dice_mod"] if attack_type == "ranged" else weapon_kw_totals["melee_dice_mod"]
    )

    hit_dice_mod = base_hit_dice_mod + keyword_hit_mod + weapon_hit_mod + cleaned_data["extra_hit_dice_mod"]

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
        "weapon": weapon,
        "attacker_weapons": list(attacker.weapons.all()),
        "attack_type": attack_type,
        "base_hit_dice_mod": base_hit_dice_mod,
        "keyword_hit_mod": keyword_hit_mod,
        "weapon_hit_mod": weapon_hit_mod,
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
        "weapon_keywords": list(weapon.keywords.all()) if weapon else [],
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
        if name in {"attacker_profile", "defender_profile", "weapon"}:
            payload[name] = form.initial.get(name) or field.queryset.first()
        else:
            payload[name] = form.initial.get(name, field.initial)

    attacker = payload.get("attacker_profile")
    if attacker and not payload.get("weapon"):
        payload["weapon"] = attacker.weapons.first()
    return payload


def calculator_view(request):
    _ensure_profiles_exist()
    results = None
    attack_form = AttackInputForm(request.POST or None, prefix="attack")

    if attack_form.is_bound and attack_form.is_valid():
        results = _build_results(attack_form.cleaned_data)
    else:
        defaults = _default_payload()
        if defaults:
            results = _build_results(defaults)
            if not attack_form.is_bound:
                attack_form.initial.update(
                    {
                        "attacker_profile": defaults["attacker_profile"],
                        "defender_profile": defaults["defender_profile"],
                        "weapon": defaults.get("weapon"),
                    }
                )

    return render(
        request,
        "calculator/index.html",
        {
            "attack_form": attack_form,
            "results": results,
            "nav_active": "calc",
        },
    )


def profile_list(request):
    _ensure_profiles_exist()
    profiles = UnitProfile.objects.prefetch_related("keywords", "weapons")
    form = UnitProfileForm(request.POST or None, prefix="profile")
    editing = None

    if request.method == "POST":
        if "delete_profile" in request.POST:
            target = get_object_or_404(UnitProfile, pk=request.POST.get("profile_id"))
            target.delete()
            return redirect("profile_list")
        else:
            if request.POST.get("profile_id"):
                editing = get_object_or_404(UnitProfile, pk=request.POST.get("profile_id"))
                form = UnitProfileForm(request.POST, prefix="profile", instance=editing)
            if form.is_valid():
                form.save()
                return redirect("profile_list")

    if request.GET.get("edit"):
        editing = get_object_or_404(UnitProfile, pk=request.GET.get("edit"))
        form = UnitProfileForm(prefix="profile", instance=editing)

    return render(
        request,
        "calculator/profiles.html",
        {
            "profiles": profiles,
            "profile_form": form,
            "editing_profile": editing,
            "nav_active": "profiles",
        },
    )


def weapon_list(request):
    weapons = Weapon.objects.prefetch_related("keywords")
    form = WeaponForm(request.POST or None, prefix="weapon")
    editing = None

    if request.method == "POST":
        if "delete_weapon" in request.POST:
            target = get_object_or_404(Weapon, pk=request.POST.get("weapon_id"))
            target.delete()
            return redirect("weapon_list")
        else:
            if request.POST.get("weapon_id"):
                editing = get_object_or_404(Weapon, pk=request.POST.get("weapon_id"))
                form = WeaponForm(request.POST, prefix="weapon", instance=editing)
            if form.is_valid():
                form.save()
                return redirect("weapon_list")

    if request.GET.get("edit"):
        editing = get_object_or_404(Weapon, pk=request.GET.get("edit"))
        form = WeaponForm(prefix="weapon", instance=editing)

    return render(
        request,
        "calculator/weapons.html",
        {
            "weapons": weapons,
            "weapon_form": form,
            "editing_weapon": editing,
            "nav_active": "weapons",
        },
    )


def keyword_list(request):
    keywords = Keyword.objects.all()
    form = KeywordForm(request.POST or None, prefix="keyword")
    editing = None

    if request.method == "POST":
        if "delete_keyword" in request.POST:
            target = get_object_or_404(Keyword, pk=request.POST.get("keyword_id"))
            target.delete()
            return redirect("keyword_list")
        else:
            if request.POST.get("keyword_id"):
                editing = get_object_or_404(Keyword, pk=request.POST.get("keyword_id"))
                form = KeywordForm(request.POST, prefix="keyword", instance=editing)
            if form.is_valid():
                form.save()
                return redirect("keyword_list")

    if request.GET.get("edit"):
        editing = get_object_or_404(Keyword, pk=request.GET.get("edit"))
        form = KeywordForm(prefix="keyword", instance=editing)

    return render(
        request,
        "calculator/keywords.html",
        {
            "keywords": keywords,
            "keyword_form": form,
            "editing_keyword": editing,
            "nav_active": "keywords",
        },
    )
