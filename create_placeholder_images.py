#!/usr/bin/env python
"""
Script pour créer des images placeholder pour toutes les œuvres
"""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import random

# Répertoire où stocker les images
BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media" / "oeuvres"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# Liste des œuvres (même noms que dans seed.json)
artworks = [
    "portrait_lune.jpg",
    "gueliz_lines.jpg",
    "poesie_visuelle.jpg",
    "rythmes_dakar.jpg",
    "oasis_rouge.jpg",
    "couleurs_nomades.jpg",
    "medina_noire.jpg",
    "atlantique_bleu.jpg",
    "scene_silencieuse.jpg",
    "symphonie_verte.jpg",
    "harmonie_douce.jpg",
    "chaos_urbain.jpg",
    "lumiere_doree.jpg",
    "frontieres_invisibles.jpg",
    "solitudes_partagees.jpg",
    "echo_nocturne.jpg",
    "poesie_visuelle.jpg",
    "fragments_ephemeres.jpg",
    "metamorphose.jpg",
]

# Couleurs de gradient
color_palettes = [
    {"start": (70, 130, 180), "end": (100, 180, 220)},  # Bleu
    {"start": (139, 69, 19), "end": (210, 180, 140)},   # Brun-or
    {"start": (128, 0, 32), "end": (220, 20, 60)},      # Rouge
    {"start": (75, 0, 130), "end": (138, 43, 226)},     # Violet
    {"start": (34, 139, 34), "end": (144, 238, 144)},   # Vert
    {"start": (255, 165, 0), "end": (255, 215, 0)},     # Orange
    {"start": (220, 20, 60), "end": (255, 105, 180)},   # Rose
]

def create_gradient_image(filename, width=300, height=300):
    """Crée une image avec un dégradé"""
    palette = random.choice(color_palettes)
    start_color = palette["start"]
    end_color = palette["end"]
    
    # Créer image
    img = Image.new("RGB", (width, height), start_color)
    pixels = img.load()
    
    # Appliquer dégradé
    for y in range(height):
        for x in range(width):
            r = int(start_color[0] + (end_color[0] - start_color[0]) * (x / width))
            g = int(start_color[1] + (end_color[1] - start_color[1]) * (x / width))
            b = int(start_color[2] + (end_color[2] - start_color[2]) * (x / width))
            pixels[x, y] = (r, g, b)
    
    # Ajouter du texte
    draw = ImageDraw.Draw(img)
    text = filename.replace(".jpg", "").replace("_", " ").title()
    
    # Essayer d'utiliser une police, sinon utiliser la police par défaut
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    # Centrer le texte
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    
    # Sauvegarder
    filepath = MEDIA_DIR / filename
    img.save(filepath)
    print(f"✅ Créé: {filepath}")

# Créer les images
print("Création des images placeholder...")
for artwork in set(artworks):  # set() pour éviter les doublons
    try:
        create_gradient_image(artwork)
    except Exception as e:
        print(f"❌ Erreur pour {artwork}: {e}")

print("\n✨ Toutes les images ont été créées!")
print(f"📁 Dossier: {MEDIA_DIR}")
