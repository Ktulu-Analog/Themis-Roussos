Thémis Roussos est une ébauche d'assistant juridique basé sur l'API Légifrance pour l'accès en temps réel aux données de Légifrance et l'API Albert de la DiNum pour les modèles d'IA.
Il est publié sous licence AGPL 3.0
La version actuelle implémente les 69 endpoints de l'API Légifrance, accessible au LLM Albert via des outils.
Parmi les fonctionnalités vous trouverez :
- interrogation en temps réel des données Légifrance
- création de timeline automatique avec les dates et infos des principaux textes pertinents
- sauvegarde automatique des conversations + timeline (pour l'instant en local au format JSON en attendant de résoudre mon problème d'endpoint Albert pour les documents)
- génération de synthèse au format .docx

Vous aurez besoin d'une clé API Albert et des acccès à l'API Légifrance via PISTE.

Cet outil peut-être adapté à d'autres endpoints compatibles OpenAI. Tout le paramétrage se fait dans le fichier .env

Pour le moment, il est aussi stable qu'une chaise à 2 pieds.
Libre à vous de rajouter les pieds manquants et de le modifier, tant que vous respectez la licence AGPL 3.0.

Version de Python utilisée pour le dev : **3.12.8** (mais ça doit fonctionner avec d'autres versions).

**Installation :**

pip install -r requirements.txt

éditez le fichier .env-exemple avec vos clés et sauvegardez-le sous .env

streamlit run app.py

-------------------------

*2026 - Pierre COUGET*
