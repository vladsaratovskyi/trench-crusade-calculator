from django.db import models


class UnitProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ranged_dice_mod = models.IntegerField(default=0, help_text="Dice modifier for ranged attacks (+/-d6).")
    melee_dice_mod = models.IntegerField(default=0, help_text="Dice modifier for melee attacks (+/-d6).")
    armor = models.IntegerField(default=0, help_text="Armor value applied to injury rolls.")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
