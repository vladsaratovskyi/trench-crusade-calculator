from django.db import models


class Keyword(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ranged_dice_mod = models.IntegerField(default=0, help_text="Dice modifier for ranged attacks (+/-d6).")
    melee_dice_mod = models.IntegerField(default=0, help_text="Dice modifier for melee attacks (+/-d6).")
    armor_mod = models.IntegerField(default=0, help_text="Armor modifier applied to injury rolls.")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UnitProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ranged_dice_mod = models.IntegerField(default=0, help_text="Dice modifier for ranged attacks (+/-d6).")
    melee_dice_mod = models.IntegerField(default=0, help_text="Dice modifier for melee attacks (+/-d6).")
    armor = models.IntegerField(default=0, help_text="Armor value applied to injury rolls.")
    keywords = models.ManyToManyField(Keyword, blank=True, related_name="unit_profiles")
    weapons = models.ManyToManyField("Weapon", blank=True, related_name="unit_profiles")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def keyword_totals(self):
        agg = {"ranged_dice_mod": 0, "melee_dice_mod": 0, "armor_mod": 0}
        for kw in self.keywords.all():
            agg["ranged_dice_mod"] += kw.ranged_dice_mod
            agg["melee_dice_mod"] += kw.melee_dice_mod
            agg["armor_mod"] += kw.armor_mod
        return agg


class Weapon(models.Model):
    ONE_HANDED = "one_handed"
    TWO_HANDED = "two_handed"
    WEAPON_TYPE_CHOICES = [
        (ONE_HANDED, "One-handed"),
        (TWO_HANDED, "Two-handed"),
    ]

    RANGE_MELEE = "melee"
    RANGE_RANGED = "ranged"
    RANGE_TYPE_CHOICES = [
        (RANGE_MELEE, "Melee"),
        (RANGE_RANGED, "Ranged"),
    ]

    name = models.CharField(max_length=100, unique=True)
    weapon_type = models.CharField(max_length=20, choices=WEAPON_TYPE_CHOICES, default=ONE_HANDED)
    range_type = models.CharField(max_length=10, choices=RANGE_TYPE_CHOICES, default=RANGE_MELEE)
    range_inches = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Range in inches for ranged weapons; leave empty for melee.",
    )
    keywords = models.ManyToManyField(Keyword, blank=True, related_name="weapons")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def keyword_totals(self):
        agg = {"ranged_dice_mod": 0, "melee_dice_mod": 0, "armor_mod": 0}
        for kw in self.keywords.all():
            agg["ranged_dice_mod"] += kw.ranged_dice_mod
            agg["melee_dice_mod"] += kw.melee_dice_mod
            agg["armor_mod"] += kw.armor_mod
        return agg
