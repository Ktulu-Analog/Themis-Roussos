"""
Module Chrono Controller
Gère tous les endpoints d'accès aux versions de textes de l'API Légifrance
Conforme à la spécification Swagger 2.4.2

4 endpoints disponibles :
- POST /chrono/textCid : Version d'un texte avec période détaillée
- POST /chrono/textCidAndElementCid : Liste des versions d'un article
- GET /chrono/textCid/{textCid} : Vérifie si un texte possède des versions
- GET /chrono/ping : Teste le contrôleur
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseAPI, ValidationError


class ChronoController(BaseAPI):
    """
    Contrôleur de gestion des versions chronologiques (Chrono Controller)
    Permet d'accéder aux différentes versions d'un texte dans le temps

    Ce contrôleur permet de :
    - Récupérer l'historique complet des versions d'un texte
    - Obtenir la liste des versions d'un article spécifique
    - Vérifier si un texte possède des versions historiques
    """

    def get_text_version(
        self,
        text_cid: str,
        date_consult: str,
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """
        Récupère le chronolegi complet d'un texte avec période détaillée

        POST /chrono/textCid

        Retourne l'historique complet des versions du texte.
        La période [start_year, end_year] aura le détail des versions chargé.

        Args:
            text_cid: CID chronologique du texte (ex: "LEGITEXT000006070721")
            date_consult: Date de référence au format YYYY-MM-DD (ex: "2021-04-15")
            start_year: Année de début pour les détails (ex: 2015)
            end_year: Année de fin pour les détails (ex: 2018)

        Returns:
            ChronolegiResponse contenant l'historique des versions

        Raises:
            ValidationError: Si les paramètres sont invalides
            LegifranceAPIError: Si la requête échoue

        Example:
            >>> chrono = ChronoController()
            >>> result = chrono.get_text_version(
            ...     text_cid="LEGITEXT000006070721",  # Code civil
            ...     date_consult="2024-01-01",
            ...     start_year=2020,
            ...     end_year=2024
            ... )
            >>> print(f"Versions trouvées: {len(result.get('versions', []))}")
        """
        # Validation des paramètres
        if not text_cid:
            raise ValidationError("text_cid est requis")

        if not date_consult:
            raise ValidationError("date_consult est requis")

        # Validation du format de date
        try:
            datetime.strptime(date_consult, "%Y-%m-%d")
        except ValueError:
            raise ValidationError(
                f"date_consult doit être au format YYYY-MM-DD, reçu: {date_consult}"
            )

        if start_year > end_year:
            raise ValidationError(
                f"start_year ({start_year}) doit être <= end_year ({end_year})"
            )

        return self.request(
            "/chrono/textCid",
            method="POST",
            body={
                "textCid": text_cid,
                "dateConsult": date_consult,
                "startYear": start_year,
                "endYear": end_year
            }
        )

    def get_article_versions(
        self,
        text_cid: str,
        element_cid: str
    ) -> Dict[str, Any]:
        """
        Récupère la liste chronologique des versions d'un article

        POST /chrono/textCidAndElementCid

        Retourne toutes les versions historiques d'un article ou d'une section
        spécifique au sein d'un texte.

        Args:
            text_cid: CID chronologique du texte (ex: "LEGITEXT000006070721")
            element_cid: CID chronologique de l'article ou section (ex: "LEGIARTI000006070721")

        Returns:
            ChronolegiResponse avec la liste des versions de l'article

        Raises:
            ValidationError: Si les paramètres sont invalides
            LegifranceAPIError: Si la requête échoue

        Example:
            >>> chrono = ChronoController()
            >>> result = chrono.get_article_versions(
            ...     text_cid="LEGITEXT000006070721",
            ...     element_cid="LEGIARTI000006436298"
            ... )
            >>> for version in result.get('versions', []):
            ...     print(f"Version du {version.get('dateDebut')}")
        """
        # Validation des paramètres
        if not text_cid:
            raise ValidationError("text_cid est requis")

        if not element_cid:
            raise ValidationError("element_cid est requis")

        return self.request(
            "/chrono/textCidAndElementCid",
            method="POST",
            body={
                "textCid": text_cid,
                "elementCid": element_cid
            }
        )

    def has_versions(self, text_cid: str) -> Dict[str, Any]:
        """
        Vérifie si un texte possède des versions chronologiques

        GET /chrono/textCid/{textCid}

        Indique rapidement si un texte possède un historique de versions
        sans récupérer toutes les données.

        Args:
            text_cid: CID chronologique du texte

        Returns:
            HasChronolegiResponse avec un booléen indiquant la présence de versions

        Raises:
            ValidationError: Si text_cid est vide
            LegifranceAPIError: Si la requête échoue

        Example:
            >>> chrono = ChronoController()
            >>> result = chrono.has_versions("LEGITEXT000006070721")
            >>> if result.get('hasChronolegi'):
            ...     print("Ce texte possède des versions historiques")
        """
        if not text_cid:
            raise ValidationError("text_cid est requis")

        return self.request(
            f"/chrono/textCid/{text_cid}",
            method="GET"
        )

    def ping(self) -> str:
        """
        Teste la disponibilité du Chrono Controller

        GET /chrono/ping

        Endpoint de santé pour vérifier que le contrôleur de versions
        est opérationnel.

        Returns:
            "pong" si le service est disponible

        Raises:
            LegifranceAPIError: Si le service n'est pas disponible

        Example:
            >>> chrono = ChronoController()
            >>> response = chrono.ping()
            >>> assert "pong" in response.lower()
        """
        response = self.request("/chrono/ping", method="GET")

        # Le endpoint retourne text/plain
        content = response.get("content", "")
        return content if content else str(response)

    # Méthodes helper et alias pour faciliter l'utilisation

    def get_text_history(
        self,
        text_cid: str,
        date_consult: Optional[str] = None,
        years_back: int = 5
    ) -> Dict[str, Any]:
        """
        Helper pour récupérer l'historique récent d'un texte

        Récupère automatiquement les versions des N dernières années
        par rapport à la date de consultation.

        Args:
            text_cid: CID chronologique du texte
            date_consult: Date de référence (défaut: aujourd'hui)
            years_back: Nombre d'années en arrière (défaut: 5)

        Returns:
            ChronolegiResponse avec l'historique

        Example:
            >>> chrono = ChronoController()
            >>> # Récupère les versions des 10 dernières années
            >>> result = chrono.get_text_history(
            ...     text_cid="LEGITEXT000006070721",
            ...     years_back=10
            ... )
        """
        if date_consult is None:
            date_consult = datetime.now().strftime("%Y-%m-%d")

        current_year = datetime.now().year
        start_year = current_year - years_back
        end_year = current_year

        return self.get_text_version(
            text_cid=text_cid,
            date_consult=date_consult,
            start_year=start_year,
            end_year=end_year
        )

    def get_all_article_versions(
        self,
        text_cid: str,
        element_cid: str
    ) -> Dict[str, Any]:
        """
        Alias pour get_article_versions (nom plus explicite)

        Args:
            text_cid: CID chronologique du texte
            element_cid: CID chronologique de l'article

        Returns:
            ChronolegiResponse avec toutes les versions de l'article
        """
        return self.get_article_versions(text_cid, element_cid)

    def check_has_history(self, text_cid: str) -> bool:
        """
        Vérifie simplement si un texte possède des versions (retourne un booléen)

        Args:
            text_cid: CID chronologique du texte

        Returns:
            True si le texte possède des versions, False sinon

        Example:
            >>> chrono = ChronoController()
            >>> if chrono.check_has_history("LEGITEXT000006070721"):
            ...     print("Historique disponible")
        """
        try:
            result = self.has_versions(text_cid)
            return result.get("hasChronolegi", False)
        except Exception:
            return False


# Alias pour compatibilité avec d'autres noms
ChronoLegiController = ChronoController
VersionController = ChronoController
