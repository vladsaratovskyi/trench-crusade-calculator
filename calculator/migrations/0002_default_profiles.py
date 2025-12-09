from django.db import migrations


def create_default_profiles(apps, schema_editor):
    UnitProfile = apps.get_model("calculator", "UnitProfile")
    defaults = [
        {"name": "Rifleman", "ranged_dice_mod": 2, "melee_dice_mod": 0, "armor": 0},
        {"name": "Bruiser", "ranged_dice_mod": 0, "melee_dice_mod": 2, "armor": 2},
    ]
    for data in defaults:
        UnitProfile.objects.get_or_create(name=data["name"], defaults=data)


class Migration(migrations.Migration):

    dependencies = [
        ("calculator", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_profiles, migrations.RunPython.noop),
    ]
