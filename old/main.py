#!/usr/bin/env python3
from calculator.logic import (
    AttackInput,
    DEFAULT_INJURY_BANDS,
    attack_outcome_probabilities,
    print_summary,
    success_probability,
)


def demo():
    print("=== Hit chance with +/- dice (2d6 system) ===\n")
    tn = 7
    for dice_mod in (-2, -1, 0, +1, +2, +3):
        p = success_probability(target_number=tn, dice_mod=dice_mod)
        rolled = 2 + abs(dice_mod)
        print(
            f"TN {tn}+ with 2d6 {dice_mod:+d}d "
            f"(roll {rolled}d6, keep {'lowest' if dice_mod<0 else 'highest'} 2): "
            f"{p*100:5.2f}%"
        )

    print("\n---\n")

    common_args = dict(
        hit_target_number=7,
        hit_dice_mod=2,       # example: -1d (roll 3, keep 2 lowest for hit)
        hit_roll_mod=0,
        injury_bands=DEFAULT_INJURY_BANDS,
        injury_dice_mod=0,
        injury_roll_mod=2,
        target_armor=0,
    )

    atk_normal = AttackInput(weapon_is_critical=False, **common_args)
    atk_crit = AttackInput(weapon_is_critical=True, **common_args)

    out_normal = attack_outcome_probabilities(atk_normal)
    out_crit = attack_outcome_probabilities(atk_crit)

    print_summary("Normal weapon (crit = +1d Injury)", out_normal)
    print_summary("Critical weapon (crit = +2d Injury)", out_crit)


if __name__ == "__main__":
    demo()
