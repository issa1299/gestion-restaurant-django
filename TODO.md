# Plan de travail - Améliorations Stock, Tables, Dashboard & Rapports

## ✅ Étape 1: Ajouter les routes manquantes dans config/urls.py
- [x] Ajouter `path("stock/", include("apps.stock.urls"))`
- [x] Ajouter `path("tables/", include("apps.tables.urls"))`
- [x] Ajouter `path("rapports/", include("apps.rapports.urls"))`

## ✅ Étape 2: Corriger les liens morts dans sidebar.html
- [x] Tables: `href="#"` → `{% url 'tables:liste' %}`
- [x] Stock: `href="#"` → `{% url 'stock:liste' %}`
- [x] Rapports: `href="#"` → `{% url 'rapports:index' %}`

## ✅ Étape 3: Améliorer la vue dashboard (apps/dashboard/views.py)
- [x] Ajouter des données réelles (CA, commandes, clients, tables)
- [x] Ajouter ventes 7 derniers jours
- [x] Ajouter stock faible
- [x] Ajouter dernières commandes

## ✅ Étape 4: Améliorer le template dashboard (templates/dashboard/index.html)
- [x] Afficher les vraies données (CA, commandes, clients, tables)
- [x] Ajouter graphique Chart.js des ventes
- [x] Afficher les dernières commandes dynamiquement
- [x] Afficher les alertes stock faible

## ✅ Étape 5: Vérification et tests
- [x] `python manage.py check` → 0 erreurs
- [x] Routes ajoutées : stock/, tables/, rapports/
- [x] Liens sidebar fonctionnels : Tables, Stock, Rapports
- [x] Dashboard avec données réelles + graphique Chart.js

