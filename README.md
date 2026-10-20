# Workflow : Ask Claude

Interroge l'API Anthropic (Claude) avec une question et retourne la réponse.

## Utilisation

- **Entrée** : `{ "question": "...", "model": "claude-sonnet-4-5" }` (model optionnel)
- **Sortie** : `{ "answer": "...", "model": "...", "input_tokens": ..., "output_tokens": ... }`

## Secret requis

La clé API Anthropic doit être définie dans le déploiement via la variable d'environnement `ANTHROPIC_API_KEY` (workspace secret du même nom dans Mistral Studio).
