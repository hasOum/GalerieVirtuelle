from django.core.management.base import BaseCommand
from galerie.models import Utilisateur, Artiste, Categorie, Oeuvre, Lieu, Exposition
from datetime import date, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        # ============================================
        # 1. CRÉER LES LIEUX D'EXPOSITIONS
        # ============================================
        lieux_data = [
            {
                'nom_lieu': 'Musée de Marrakech',
                'adresse': 'Place Ben Youssef, Medina',
                'ville': 'Marrakech',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Galerie Diverarts',
                'adresse': 'Rue Allal Ben Abdellah, Gueliz',
                'ville': 'Marrakech',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Villa des Arts de Casablanca',
                'adresse': 'Boulevard Brahim Roudani',
                'ville': 'Casablanca',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Galerie Belghazi',
                'adresse': 'Rue Remila, Medina',
                'ville': 'Fès',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Museum Dar Jamai',
                'adresse': 'Place Bab Jeloud',
                'ville': 'Meknès',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Galerie Aïna',
                'adresse': 'Rue Sultan Mabrouk',
                'ville': 'Casablanca',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Espace Kasr Al Nakhil',
                'adresse': 'Skhirat',
                'ville': 'Rabat',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Galerie Contemporary Art',
                'adresse': 'Avenue Mohamed V',
                'ville': 'Tanger',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Musée Tamazight',
                'adresse': 'Rue de la République',
                'ville': 'Ifrane',
                'pays': 'Maroc'
            },
            {
                'nom_lieu': 'Espace Culturel Essaouira',
                'adresse': 'Avenue du Beachfront',
                'ville': 'Essaouira',
                'pays': 'Maroc'
            },
        ]
        
        created_count = 0
        for lieu_data in lieux_data:
            lieu, created = Lieu.objects.get_or_create(
                nom_lieu=lieu_data['nom_lieu'],
                defaults={
                    'adresse': lieu_data['adresse'],
                    'ville': lieu_data['ville'],
                    'pays': lieu_data['pays']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'✅ Créé: {lieu.nom_lieu} - {lieu.ville}')
            else:
                self.stdout.write(f'⏭️  Déjà existant: {lieu.nom_lieu}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} lieux d\'exposition ajoutés à la base de données!'))
        
        # ============================================
        # 2. CRÉER LES CATÉGORIES
        # ============================================
        cat_peinture, _ = Categorie.objects.get_or_create(
            nom_categorie='Peinture',
            defaults={'description': 'Œuvres de peinture'}
        )
        cat_sculpture, _ = Categorie.objects.get_or_create(
            nom_categorie='Sculpture',
            defaults={'description': 'Sculptures'}
        )
        
        # ============================================
        # 3. CRÉER UN ARTISTE
        # ============================================
        user_artiste, user_created = Utilisateur.objects.get_or_create(
            username='picasso',
            defaults={
                'email': 'picasso@galerie.com',
                'first_name': 'Pablo',
                'last_name': 'Picasso',
                'role': 'artiste'
            }
        )
        
        if user_created:
            user_artiste.set_password('password123')
            user_artiste.save()
            self.stdout.write(f'✅ Créé: Utilisateur {user_artiste.username}')
        else:
            self.stdout.write(f'⏭️  Déjà existant: Utilisateur {user_artiste.username}')
        
        artiste, artiste_created = Artiste.objects.get_or_create(
            user=user_artiste,
            defaults={
                'nom': 'Pablo Picasso',
                'nationalite': 'Espagnol',
                'biographie': 'Artiste célèbre'
            }
        )
        
        if artiste_created:
            self.stdout.write(f'✅ Créé: Artiste {artiste.nom}')
        else:
            self.stdout.write(f'⏭️  Déjà existant: Artiste {artiste.nom}')
        
        # ============================================
        # 4. CRÉER UNE ŒUVRE
        # ============================================
        oeuvre, oeuvre_created = Oeuvre.objects.get_or_create(
            titre='Guernica',
            defaults={
                'description': 'Chef-d\'œuvre cubiste',
                'technique': 'Huile sur toile',
                'annee_creation': 1937,
                'prix': 1000000.00,
                'stock': 1,
                'statut': 'valide',
                'artiste': artiste,
                'categorie': cat_peinture
            }
        )
        
        if oeuvre_created:
            self.stdout.write(f'✅ Créée: Œuvre {oeuvre.titre}')
        else:
            self.stdout.write(f'⏭️  Déjà existante: Œuvre {oeuvre.titre}')
        
        # ============================================
        # 5. CRÉER LES EXPOSITIONS AVEC LIEUX
        # ============================================
        expositions_data = [
            {
                'nom': 'Printemps des Créateurs',
                'description': 'Une exposition célébrant les talents émergents de la région',
                'lieu': 'Musée de Marrakech',
                'date_debut': date(2026, 3, 1),
                'date_fin': date(2026, 3, 31)
            },
            {
                'nom': 'Transformations Urbaines',
                'description': 'Art contemporain reflétant les changements urbains',
                'lieu': 'Galerie Diverarts',
                'date_debut': date(2026, 2, 15),
                'date_fin': date(2026, 3, 15)
            },
            {
                'nom': 'Échos de la Nature',
                'description': 'Expositions sur la relation entre l\'art et l\'environnement',
                'lieu': 'Villa des Arts de Casablanca',
                'date_debut': date(2026, 1, 20),
                'date_fin': date(2026, 2, 28)
            },
            {
                'nom': 'Nuits Brillantes',
                'description': 'Photographies et installations lumineuses',
                'lieu': 'Galerie Belghazi',
                'date_debut': date(2026, 4, 1),
                'date_fin': date(2026, 4, 30)
            },
            {
                'nom': 'Limites Fragmentées',
                'description': 'Exploration des limites entre réalité et imaginaire',
                'lieu': 'Museum Dar Jamai',
                'date_debut': date(2026, 2, 1),
                'date_fin': date(2026, 3, 31)
            },
            {
                'nom': 'Photographie & Silence',
                'description': 'Une collection de photographies introspectives',
                'lieu': 'Galerie Aïna',
                'date_debut': date(2026, 1, 10),
                'date_fin': date(2026, 2, 28)
            },
            {
                'nom': 'Couleurs du Sud',
                'description': 'Peintures inspirées par les paysages marocains',
                'lieu': 'Espace Kasr Al Nakhil',
                'date_debut': date(2026, 3, 15),
                'date_fin': date(2026, 5, 15)
            },
            {
                'nom': 'Abstractions Modernes',
                'description': 'Art abstrait contemporain',
                'lieu': 'Galerie Contemporary Art',
                'date_debut': date(2026, 2, 1),
                'date_fin': date(2026, 4, 1)
            },
            {
                'nom': 'Regards Contemporains',
                'description': 'Une perspective nouvelle sur l\'art moderne',
                'lieu': 'Musée Tamazight',
                'date_debut': date(2026, 1, 25),
                'date_fin': date(2026, 3, 25)
            },
            {
                'nom': 'Matière & Relief',
                'description': 'Sculptures et installations texturées',
                'lieu': 'Espace Culturel Essaouira',
                'date_debut': date(2026, 4, 10),
                'date_fin': date(2026, 5, 31)
            },
        ]
        
        expo_created_count = 0
        for expo_data in expositions_data:
            lieu = Lieu.objects.get(nom_lieu=expo_data['lieu'])
            expo, created = Exposition.objects.get_or_create(
                nom_exposition=expo_data['nom'],
                defaults={
                    'description': expo_data['description'],
                    'date_debut': expo_data['date_debut'],
                    'date_fin': expo_data['date_fin'],
                    'lieu': lieu
                }
            )
            if created:
                # Ajouter une œuvre à l'exposition
                expo.oeuvres.add(oeuvre)
                expo_created_count += 1
                statut = expo.statut
                self.stdout.write(f'✅ Créée: {expo.nom_exposition} ({statut}) - {lieu.ville}')
            else:
                self.stdout.write(f'⏭️  Déjà existante: {expo.nom_exposition}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {expo_created_count} expositions ajoutées à la base de données!'))
        self.stdout.write(self.style.SUCCESS('✅ Tous les données ont été créées avec succès !'))

