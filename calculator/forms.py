from django import forms

from .models import Keyword, UnitProfile, Weapon

ATTACK_TYPE_CHOICES = (
    ("ranged", "Ranged"),
    ("melee", "Melee"),
)


class AttackInputForm(forms.Form):
    attacker_profile = forms.ModelChoiceField(
        label="Attacker profile",
        queryset=UnitProfile.objects.none(),
        empty_label=None,
    )
    weapon = forms.ModelChoiceField(
        label="Weapon (optional)",
        queryset=Weapon.objects.none(),
        required=False,
    )
    defender_profile = forms.ModelChoiceField(
        label="Target profile",
        queryset=UnitProfile.objects.none(),
        empty_label=None,
    )
    attack_type = forms.ChoiceField(label="Attack type", choices=ATTACK_TYPE_CHOICES, initial="ranged")

    hit_target_number = forms.IntegerField(label="Hit target number (TN)", min_value=2, initial=7)
    extra_hit_dice_mod = forms.IntegerField(label="Additional hit dice modifier (+/-d6)", initial=0)
    hit_roll_mod = forms.IntegerField(label="Hit roll modifier", initial=0)
    injury_dice_mod = forms.IntegerField(label="Injury dice modifier (+/-d6)", initial=0)
    injury_roll_mod = forms.IntegerField(label="Injury roll modifier", initial=2)
    extra_target_armor = forms.IntegerField(label="Additional armor modifier", initial=0)
    weapon_is_critical = forms.BooleanField(
        label="Critical weapon (+2d injury on crit instead of +1d)",
        required=False,
        initial=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = UnitProfile.objects.all()
        self.fields["attacker_profile"].queryset = qs
        self.fields["defender_profile"].queryset = qs
        self.fields["weapon"].queryset = Weapon.objects.all()
        if not self.is_bound and qs.exists():
            first = qs.first()
            self.initial.setdefault("attacker_profile", first)
            self.initial.setdefault("defender_profile", first)


class UnitProfileForm(forms.ModelForm):
    keywords = forms.ModelMultipleChoiceField(
        label="Keywords",
        queryset=Keyword.objects.none(),
        required=False,
        help_text="Select any keywords that modify this profile.",
        widget=forms.SelectMultiple(attrs={"size": 4}),
    )
    weapons = forms.ModelMultipleChoiceField(
        label="Weapons",
        queryset=Weapon.objects.none(),
        required=False,
        help_text="Assign weapons this profile can use.",
        widget=forms.SelectMultiple(attrs={"size": 4}),
    )

    class Meta:
        model = UnitProfile
        fields = ["name", "ranged_dice_mod", "melee_dice_mod", "armor", "keywords", "weapons"]
        labels = {
            "name": "Profile name",
            "ranged_dice_mod": "Ranged attack dice mod (+/-d6)",
            "melee_dice_mod": "Melee attack dice mod (+/-d6)",
            "armor": "Armor (applied to injury)",
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        return name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["keywords"].queryset = Keyword.objects.all()
        self.fields["weapons"].queryset = Weapon.objects.all()


class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keyword
        fields = ["name", "ranged_dice_mod", "melee_dice_mod", "armor_mod"]
        labels = {
            "name": "Keyword name",
            "ranged_dice_mod": "Ranged dice mod (+/-d6)",
            "melee_dice_mod": "Melee dice mod (+/-d6)",
            "armor_mod": "Armor modifier",
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class WeaponForm(forms.ModelForm):
    keywords = forms.ModelMultipleChoiceField(
        label="Keywords",
        queryset=Keyword.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 4}),
    )

    class Meta:
        model = Weapon
        fields = ["name", "weapon_type", "range_type", "range_inches", "keywords"]
        labels = {
            "name": "Weapon name",
            "weapon_type": "Type",
            "range_type": "Range type",
            "range_inches": "Range (inches, for ranged)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["keywords"].queryset = Keyword.objects.all()

    def clean_name(self):
        return self.cleaned_data["name"].strip()
