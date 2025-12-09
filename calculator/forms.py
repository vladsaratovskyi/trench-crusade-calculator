from django import forms


class AttackInputForm(forms.Form):
    hit_target_number = forms.IntegerField(label="Hit target number (TN)", min_value=2, initial=7)
    hit_dice_mod = forms.IntegerField(label="Hit dice modifier (+/-d6)", initial=2)
    hit_roll_mod = forms.IntegerField(label="Hit roll modifier", initial=0)
    injury_dice_mod = forms.IntegerField(label="Injury dice modifier (+/-d6)", initial=0)
    injury_roll_mod = forms.IntegerField(label="Injury roll modifier", initial=2)
    target_armor = forms.IntegerField(label="Target armor", initial=0)
    weapon_is_critical = forms.BooleanField(
        label="Critical weapon (+2d injury on crit instead of +1d)",
        required=False,
        initial=False,
    )
