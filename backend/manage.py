#!/usr/bin/env python
"""Outil de ligne de commande Django pour gérer le projet."""
import os
import sys

def main():
    """Point d'entrée pour les commandes administratives."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django n'est pas installé. Activez votre environnement virtuel."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()