from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Tuple

KEEP_DICES = 2
DICE_SIDES = 6
CRIT_RESULT = 12


@dataclass(frozen=True)
class InjuryBand:
    min_value: int
    max_value: Optional[int]  # None means "no upper limit"
    label: str

    def matches(self, value: int) -> bool:
        if value < self.min_value:
            return False
        if self.max_value is None:
            return True
        return value <= self.max_value


DEFAULT_INJURY_BANDS: List[InjuryBand] = [
    InjuryBand(2, 6, "Flesh Wound"),
    InjuryBand(7, 8, "Down"),
    InjuryBand(9, None, "Out of Action"),
]


def dice_sum_distribution(
    num_dice: int,
    keep_highest: bool = True,
) -> Dict[int, float]:
    if num_dice <= 0:
        raise ValueError("num_dice must be >= 1")

    counts = Counter()
    total_outcomes = DICE_SIDES ** num_dice

    for rolls in product(range(1, DICE_SIDES + 1), repeat=num_dice):
        srt = sorted(rolls)
        kept = srt[-KEEP_DICES:] if keep_highest else srt[:KEEP_DICES]
        counts[sum(kept)] += 1

    return {total: count / total_outcomes for total, count in sorted(counts.items())}


def success_probability(
    target_number: int,
    dice_mod: int = 0,
    roll_mod: int = 0,
) -> float:
    dices_rolled = KEEP_DICES + abs(dice_mod)
    keep_highest = dice_mod >= 0

    dist = dice_sum_distribution(dices_rolled, keep_highest=keep_highest)

    prob = 0.0
    for value, p in dist.items():
        if value + roll_mod >= target_number:
            prob += p

    return prob


def injury_distribution(
    injury_bands: List[InjuryBand],
    dice_mod: int = 0,
    roll_mod: int = 0,
    target_armor: int = 0,
) -> Dict[str, float]:
    num_rolled = KEEP_DICES + abs(dice_mod)
    keep_highest = dice_mod >= 0

    dist = dice_sum_distribution(num_rolled, keep_highest=keep_highest)

    result: Dict[str, float] = {band.label: 0.0 for band in injury_bands}

    for value, p in dist.items():
        total = value + roll_mod - target_armor
        for band in injury_bands:
            if band.matches(total):
                result[band.label] += p
                break

    return result


@dataclass
class AttackInput:
    # Hit (Success) roll
    hit_target_number: int           # e.g. 7+ to hit
    hit_dice_mod: int = 0            # +Xd / -Xd dice
    hit_roll_mod: int = 0            # flat modifier to the kept sum

    # Crit rules
    weapon_is_critical: bool = False # if True, crit = +2d Injury instead of +1d

    # Injury roll
    injury_bands: List[InjuryBand] | None = None
    injury_dice_mod: int = 0         # base +/- dice on Injury (before crit bonus)
    injury_roll_mod: int = 0         # flat modifier to Injury sum
    target_armor: int = 0            # armor to subtract from Injury

    def validate(self):
        if not self.injury_bands:
            raise ValueError("injury_bands must be provided.")


def hit_branches(
    hit_dice_mod: int,
) -> Dict[Tuple[int, int], float]:
    num_rolled = KEEP_DICES + abs(hit_dice_mod)
    total_outcomes = DICE_SIDES ** num_rolled
    counts = Counter()

    for rolls in product(range(1, DICE_SIDES + 1), repeat=num_rolled):
        srt = sorted(rolls)
        lowest = srt[:KEEP_DICES]
        highest = srt[-KEEP_DICES:]
        kept = highest if hit_dice_mod >= 0 else lowest
        kept_sum = sum(kept)
        highest_sum = sum(highest)
        counts[(kept_sum, highest_sum)] += 1

    return {k: c / total_outcomes for k, c in counts.items()}


def attack_outcome_probabilities(attack: AttackInput) -> Dict[str, float]:
    attack.validate()

    result: Dict[str, float] = {"Miss": 0.0}
    for band in attack.injury_bands:
        result.setdefault(band.label, 0.0)

    branches = hit_branches(attack.hit_dice_mod)

    for (kept_sum, highest_sum), p_raw in branches.items():
        total_hit = kept_sum + attack.hit_roll_mod

        # Miss
        if total_hit < attack.hit_target_number:
            result["Miss"] += p_raw
            continue

        # Crit logic (based on highest 2 dice, even with penalties)
        extra_dice_from_crit = 0
        if highest_sum == CRIT_RESULT:
            extra_dice_from_crit = 2 if attack.weapon_is_critical else 1

        # Final Injury dice modifier on this branch
        branch_injury_dice_mod = attack.injury_dice_mod + extra_dice_from_crit

        cond_injury = injury_distribution(
            injury_bands=attack.injury_bands,
            dice_mod=branch_injury_dice_mod,
            roll_mod=attack.injury_roll_mod,
            target_armor=attack.target_armor,
        )

        for label, p_injury in cond_injury.items():
            result[label] += p_raw * p_injury

    return result


def format_percent(p: float) -> str:
    return f"{p*100:5.2f}%"


def print_summary(name: str, outcome: Dict[str, float]):
    miss = outcome.get("Miss", 0.0)
    any_injury = 1.0 - miss

    down = outcome.get("Down", 0.0)
    ooa = outcome.get("Out of Action", 0.0)

    print(f"=== {name} ===")
    for label, p in outcome.items():
        print(f"  {label:14s}: {format_percent(p)}")
    print("  -------------------------")
    print(f"  Any injury      : {format_percent(any_injury)}")
    print(f"  Down : {format_percent(down)}")
    print(f"  OOA : {format_percent(ooa)}")
    print()
