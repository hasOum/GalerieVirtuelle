from django.core.management.base import BaseCommand
from galerie.models import Utilisateur, Artiste, Categorie, Oeuvre, Lieu
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        # Créer catégories
        cat_peinture, _ = Categorie.objects.get_or_create(
            nom_categorie='Peinture',
            defaults={'description': 'Œuvres de peinture'}
        )
        cat_sculpture, _ = Categorie.objects.get_or_create(
            nom_categorie='Sculpture',
            defaults={'description': 'Sculptures'}
        )
        
        # Créer un artiste
        user_artiste = Utilisateur.objects.create_user(
            username='picasso',
            email='picasso@galerie.com',
            password='password123',
            first_name='Pablo',
            last_name='Picasso',
            role='artiste'
        )
        
        artiste = Artiste.objects.create(
            utilisateur=user_artiste,
            nationalite='Espagnol',
            biographie='Artiste célèbre'
        )
        
        # Créer une œuvre
        Oeuvre.objects.create(
            titre='Guernica',
            description='Chef-d\'œuvre cubiste',
            technique='Huile sur toile',
            annee_creation=1937,
            prix=1000000.00,
            stock=1,
            statut='valide',
            artiste=artiste,
            categorie=cat_peinture
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Données de test créées !'))
