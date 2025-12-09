from django.shortcuts import render

from .forms import AttackInputForm
from .logic import (
    AttackInput,
    DEFAULT_INJURY_BANDS,
    attack_outcome_probabilities,
    success_probability,
)


def _as_percent(value: float) -> str:
    return f"{value*100:.2f}%"


def _build_results(cleaned_data):
    attack = AttackInput(
        hit_target_number=cleaned_data["hit_target_number"],
        hit_dice_mod=cleaned_data["hit_dice_mod"],
        hit_roll_mod=cleaned_data["hit_roll_mod"],
        weapon_is_critical=cleaned_data.get("weapon_is_critical", False),
        injury_bands=DEFAULT_INJURY_BANDS,
        injury_dice_mod=cleaned_data["injury_dice_mod"],
        injury_roll_mod=cleaned_data["injury_roll_mod"],
        target_armor=cleaned_data["target_armor"],
    )

    outcome = attack_outcome_probabilities(attack)
    hit_prob = success_probability(
        target_number=cleaned_data["hit_target_number"],
        dice_mod=cleaned_data["hit_dice_mod"],
        roll_mod=cleaned_data["hit_roll_mod"],
    )
    any_injury = 1.0 - outcome.get("Miss", 0.0)

    return {
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


def calculator_view(request):
    if request.method == "POST":
        form = AttackInputForm(request.POST)
        results = _build_results(form.cleaned_data) if form.is_valid() else None
    else:
        form = AttackInputForm()
        defaults = {name: field.initial for name, field in form.fields.items()}
        results = _build_results(defaults)

    return render(request, "calculator/index.html", {"form": form, "results": results})
