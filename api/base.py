"""
Module de base pour l'API Légifrance
Gère l'authentification OAuth2 et les requêtes HTTP
Conforme à la spécification Swagger 2.4.2
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

import httpx


# Configuration du logging
logger = logging.getLogger(__name__)


class LegifranceAPIError(Exception):
    """Exception de base pour les erreurs API Légifrance"""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(LegifranceAPIError):
    """Exception pour les erreurs d'authentification OAuth2"""
    pass


class RateLimitError(LegifranceAPIError):
    """Exception pour les erreurs de limitation de débit"""
    pass


class ValidationError(LegifranceAPIError):
    """Exception pour les erreurs de validation des paramètres"""
    pass


class BaseAPI:
    """
    Classe de base pour l'API Légifrance
    Gère l'authentification OAuth2 et les requêtes HTTP

    Conforme à la spécification Swagger 2.4.2
    Base URL: https://api.piste.gouv.fr/dila/legifrance/lf-engine-app
    """

    # URLs de production (uniquement production, pas de sandbox)
    PRODUCTION_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
    OAUTH_URL = "https://oauth.piste.gouv.fr/api/oauth/token"

    # Configuration des timeouts et retry
    DEFAULT_TIMEOUT = 30.0
    CONNECT_TIMEOUT = 10.0
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2  # Backoff exponentiel: 1s, 2s, 4s

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialise le client API de base

        Args:
            client_id: Client ID OAuth (ou depuis LEGIFRANCE_CLIENT_ID)
            client_secret: Client Secret OAuth (ou depuis LEGIFRANCE_CLIENT_SECRET)
            timeout: Timeout pour les requêtes HTTP (défaut: 30s)
            max_retries: Nombre maximum de tentatives en cas d'échec (défaut: 3)

        Raises:
            ValidationError: Si les identifiants OAuth sont manquants
        """
        self.client_id = client_id or os.getenv("LEGIFRANCE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LEGIFRANCE_CLIENT_SECRET")
        self.base_url = self.PRODUCTION_BASE_URL
        self.max_retries = max_retries

        if not self.client_id or not self.client_secret:
            raise ValidationError(
                "Identifiants OAuth manquants. Définissez LEGIFRANCE_CLIENT_ID "
                "et LEGIFRANCE_CLIENT_SECRET dans l'environnement ou passez-les en paramètres."
            )

        # Gestion du token OAuth2
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self._token_type: str = "Bearer"

        # Client HTTP synchrone avec configuration optimisée
        timeout_config = httpx.Timeout(
            timeout or self.DEFAULT_TIMEOUT,
            connect=self.CONNECT_TIMEOUT
        )

        self.http = httpx.Client(
            timeout=timeout_config,
            follow_redirects=True,
            http2=True,  # Support HTTP/2 pour de meilleures performances
        )

        logger.info(f"Client API Légifrance initialisé (base_url={self.base_url})")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Obtient un token OAuth2 valide (utilise le cache si disponible)

        Args:
            force_refresh: Force le renouvellement du token même s'il est valide

        Returns:
            Token d'accès valide

        Raises:
            AuthenticationError: Si l'authentification échoue
        """
        # Vérifier si le token en cache est encore valide (marge de 60s)
        if not force_refresh and self._token and time.time() < (self._token_expiry - 60):
            logger.debug("Utilisation du token en cache")
            return self._token

        logger.info("Demande d'un nouveau token OAuth2")

        try:
            response = self.http.post(
                self.OAUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "openid",
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()

            data = response.json()

            # Validation de la réponse
            if "access_token" not in data:
                raise AuthenticationError(
                    "La réponse OAuth ne contient pas de access_token",
                    response_data=data
                )

            self._token = data["access_token"]
            self._token_type = data.get("token_type", "Bearer")
            expires_in = data.get("expires_in", 3600)
            self._token_expiry = time.time() + expires_in

            logger.info(f"Token OAuth2 obtenu avec succès (expire dans {expires_in}s)")
            return self._token

        except httpx.HTTPStatusError as e:
            error_msg = f"Échec de l'authentification OAuth2: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {e.response.text}"

            logger.error(error_msg)
            raise AuthenticationError(
                error_msg,
                status_code=e.response.status_code,
                response_data=e.response.text
            )

        except httpx.RequestError as e:
            error_msg = f"Erreur réseau lors de l'authentification: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)

        except Exception as e:
            error_msg = f"Erreur inattendue lors de l'authentification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AuthenticationError(error_msg)

    def _build_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Construit les headers HTTP pour une requête

        Args:
            additional_headers: Headers additionnels à ajouter

        Returns:
            Dictionnaire des headers
        """
        token = self.get_access_token()

        headers = {
            "Authorization": f"{self._token_type} {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "legifrance-api-client/2.4.2",
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def request(
        self,
        path: str,
        method: str = "POST",
        body: Optional[Union[Dict[str, Any], str]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_on_auth_failure: bool = True,
    ) -> Dict[str, Any]:
        """
        Effectue une requête API générique avec retry automatique

        Args:
            path: Chemin de l'endpoint (ex: "/search", "/consult/getArticle")
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            body: Corps de la requête (dict pour JSON ou str pour autre format)
            params: Paramètres de requête URL
            headers: Headers HTTP additionnels
            retry_on_auth_failure: Réessayer automatiquement si erreur 401

        Returns:
            Réponse JSON de l'API

        Raises:
            AuthenticationError: Si l'authentification échoue
            RateLimitError: Si la limite de débit est atteinte
            ValidationError: Si les paramètres sont invalides
            LegifranceAPIError: Pour toute autre erreur API
        """
        url = f"{self.base_url}{path}"
        method = method.upper()

        logger.debug(f"Requête {method} {path}")

        # Préparer le corps de la requête
        json_body = None
        content = None

        if body is not None:
            if isinstance(body, dict):
                json_body = body
            elif isinstance(body, str):
                content = body

        # Tentatives avec retry
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                request_headers = self._build_headers(headers)

                response = self.http.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json_body,
                    content=content,
                    params=params,
                )

                # Gestion spécifique des codes de statut
                if response.status_code == 401 and retry_on_auth_failure and attempt == 1:
                    logger.warning("Token expiré (401), renouvellement...")
                    self.get_access_token(force_refresh=True)
                    continue

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        f"Limite de débit atteinte. Réessayez dans {retry_after}s",
                        status_code=429,
                        response_data={"retry_after": retry_after}
                    )

                response.raise_for_status()

                # Gérer les réponses vides ou non-JSON
                if response.status_code == 204:
                    return {}

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    result = response.json()
                    logger.debug(f"Requête {method} {path} réussie")
                    return result
                else:
                    # Réponse non-JSON (ex: text/plain pour /ping)
                    return {"content": response.text, "content_type": content_type}

            except httpx.HTTPStatusError as e:
                last_exception = e

                if e.response.status_code == 401 and retry_on_auth_failure and attempt < self.max_retries:
                    logger.warning(f"Erreur 401 (tentative {attempt}/{self.max_retries}), renouvellement du token...")
                    self.get_access_token(force_refresh=True)
                    continue

                if e.response.status_code == 429:
                    raise  # RateLimitError déjà levée ci-dessus

                if e.response.status_code >= 500 and attempt < self.max_retries:
                    # Retry sur erreurs serveur
                    wait_time = self.RETRY_BACKOFF_FACTOR ** (attempt - 1)
                    logger.warning(
                        f"Erreur serveur {e.response.status_code} "
                        f"(tentative {attempt}/{self.max_retries}), "
                        f"nouvelle tentative dans {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

                # Construire un message d'erreur détaillé
                error_msg = f"Erreur HTTP {e.response.status_code} sur {method} {path}"
                error_detail = None

                try:
                    error_detail = e.response.json()
                    error_msg += f"\nDétail: {json.dumps(error_detail, ensure_ascii=False, indent=2)}"
                except:
                    error_msg += f"\nRéponse: {e.response.text[:500]}"

                logger.error(error_msg)

                # Lever l'exception appropriée
                if e.response.status_code == 400:
                    raise ValidationError(
                        error_msg,
                        status_code=e.response.status_code,
                        response_data=error_detail
                    )
                elif e.response.status_code == 401:
                    raise AuthenticationError(
                        error_msg,
                        status_code=e.response.status_code,
                        response_data=error_detail
                    )
                else:
                    raise LegifranceAPIError(
                        error_msg,
                        status_code=e.response.status_code,
                        response_data=error_detail
                    )

            except httpx.RequestError as e:
                last_exception = e

                if attempt < self.max_retries:
                    wait_time = self.RETRY_BACKOFF_FACTOR ** (attempt - 1)
                    logger.warning(
                        f"Erreur réseau (tentative {attempt}/{self.max_retries}): {str(e)}, "
                        f"nouvelle tentative dans {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

                error_msg = f"Erreur réseau lors de la requête {method} {path}: {str(e)}"
                logger.error(error_msg)
                raise LegifranceAPIError(error_msg)

        # Si on arrive ici, toutes les tentatives ont échoué
        error_msg = f"Échec de la requête {method} {path} après {self.max_retries} tentatives"
        if last_exception:
            error_msg += f": {str(last_exception)}"

        logger.error(error_msg)
        raise LegifranceAPIError(error_msg)

    def ping(self) -> str:
        """
        Teste la connectivité avec l'API (endpoint /list/ping)

        Returns:
            "pong" si le service est disponible

        Raises:
            LegifranceAPIError: Si le service n'est pas disponible
        """
        try:
            response = self.request("/list/ping", method="GET")
            content = response.get("content", "")

            if "pong" in content.lower():
                logger.info("Ping réussi: service disponible")
                return content
            else:
                logger.warning(f"Ping: réponse inattendue: {content}")
                return content
        except Exception as e:
            logger.error(f"Ping échoué: {str(e)}")
            raise LegifranceAPIError(f"Service indisponible: {str(e)}")

    def get_commit_id(self) -> Dict[str, Any]:
        """
        Récupère les informations de déploiement et de versioning (/misc/commitId)

        Returns:
            Informations sur la version de l'API déployée
        """
        return self.request("/misc/commitId", method="GET")

    def close(self):
        """Ferme le client HTTP et libère les ressources"""
        if self.http:
            logger.info("Fermeture du client HTTP")
            self.http.close()

    def __enter__(self):
        """Support du context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager"""
        self.close()
        return False

    def __del__(self):
        """Nettoyage lors de la destruction de l'objet"""
        try:
            self.close()
        except:
            pass

    def __repr__(self) -> str:
        """Représentation en chaîne de l'objet"""
        return f"<BaseAPI(base_url='{self.base_url}', client_id='{self.client_id[:8]}...')>"
