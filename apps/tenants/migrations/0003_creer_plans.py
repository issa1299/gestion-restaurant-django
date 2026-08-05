from django.db import migrations


def creer_plans(apps, schema_editor):
    Plan = apps.get_model("tenants", "Plan")
    Restaurant = apps.get_model("tenants", "Restaurant")

    plans = [
        {
            "nom": "Essentiel",
            "prix_mensuel": 10000,
            "nb_utilisateurs_max": 1,
            "nb_caisses_max": 1,
            "modules": ["menu", "commandes", "caisse", "clients", "tables", "notifications"],
            "ordre": 1,
        },
        {
            "nom": "Pro",
            "prix_mensuel": 25000,
            "nb_utilisateurs_max": 5,
            "nb_caisses_max": 3,
            "modules": ["menu", "commandes", "caisse", "clients", "tables", "notifications",
                        "stock", "livraison", "rapports", "multi_caisses"],
            "ordre": 2,
        },
        {
            "nom": "Premium",
            "prix_mensuel": 50000,
            "nb_utilisateurs_max": 20,
            "nb_caisses_max": 10,
            "modules": ["menu", "commandes", "caisse", "clients", "tables", "notifications",
                        "stock", "livraison", "rapports", "multi_caisses", "cuisine"],
            "ordre": 3,
        },
    ]

    for data in plans:
        Plan.objects.get_or_create(nom=data["nom"], defaults=data)

    # Plan par défaut pour les restaurants existants : Essentiel
    essentiel = Plan.objects.filter(nom="Essentiel").first()
    if essentiel:
        Restaurant.objects.filter(plan__isnull=True).update(plan=essentiel)


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0002_plan_restaurant_plan"),
    ]

    operations = [
        migrations.RunPython(creer_plans, migrations.RunPython.noop),
    ]
