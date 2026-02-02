"""
Module List Controller
Gère tous les endpoints de listage de l'API Légifrance
13 endpoints disponibles
"""

from typing import Dict, Any, Optional, List
from .base import BaseAPI


class ListController(BaseAPI):
    """
    Contrôleur de listage
    Permet de lister les codes, conventions collectives, etc.
    """

    def list_codes(
        self,
        page_number: int = 1,
        page_size: int = 10,
        code_name: Optional[str] = None,
        states: Optional[List[str]] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des codes disponibles

        POST /list/code

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            code_name: Titre de code à chercher (optional)
            states: États juridiques (optional, ex: ['VIGUEUR', 'ABROGE'])
            sort: Ordre de tri (optional, ex: "TITLE_ASC")

        Returns:
            Liste paginée des codes
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if code_name:
            body["codeName"] = code_name
        if states:
            body["states"] = states
        if sort:
            body["sort"] = sort

        return self.request("/list/code", method="POST", body=body)

    def list_conventions(
        self,
        page_number: int = 1,
        page_size: int = 10,
        idcc: Optional[str] = None,
        titre: Optional[str] = None,
        key_words: Optional[List[str]] = None,
        legal_status: Optional[List[str]] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste paginée des conventions collectives

        POST /list/conventions

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            idcc: IDCC pour filtrer (optional)
            titre: Texte à rechercher dans les titres (optional)
            key_words: Mots clés (optional)
            legal_status: États juridiques (optional)
            sort: Ordre de tri (optional, ex: "DATE_PUBLI_ASC")
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if idcc:
            body["idcc"] = idcc
        if titre:
            body["titre"] = titre
        if key_words:
            body["keyWords"] = key_words
        if legal_status:
            body["legalStatus"] = legal_status
        if sort:
            body["sort"] = sort

        return self.request("/list/conventions", method="POST", body=body)

    def list_loda(
        self,
        page_number: int = 1,
        page_size: int = 10,
        natures: Optional[List[str]] = None,
        legal_status: Optional[List[str]] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des lois et décrets autonomes

        POST /list/loda

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            natures: Natures (optional, ex: ['LOI', 'ORDONNANCE', 'DECRET'])
            legal_status: États juridiques (optional)
            sort: Ordre de tri (optional, ex: "PUBLICATION_DATE_ASC")
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if natures:
            body["natures"] = natures
        if legal_status:
            body["legalStatus"] = legal_status
        if sort:
            body["sort"] = sort

        return self.request("/list/loda", method="POST", body=body)

    def list_docs_admins(self, years: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Liste des documents administratifs pour une période donnée

        POST /list/docsAdmins

        Args:
            years: Liste des années recherchées (optional)

        Returns:
            Liste des documents administratifs
        """
        body = {}
        if years:
            body["years"] = years

        return self.request("/list/docsAdmins", method="POST", body=body)

    def list_bodmr(
        self,
        page_number: int = 1,
        page_size: int = 10,
        years: Optional[List[int]] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des bulletins officiels des décorations, médailles et récompenses

        POST /list/bodmr

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            years: Années à filtrer (optional)
            sort: Ordre de tri (optional, ex: "PUBLICATION_DATE_ASC")
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if years:
            body["years"] = years
        if sort:
            body["sort"] = sort

        return self.request("/list/bodmr", method="POST", body=body)

    def list_bocc(
        self,
        page_number: int = 1,
        page_size: int = 10,
        id_global_bocc: Optional[str] = None,
        interval_publication: Optional[str] = None,
        sort_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des bulletins officiels des conventions collectives

        POST /list/bocc

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            id_global_bocc: ID du BOCC global (optional)
            interval_publication: Intervalle de publication (optional, ex: "01/01/2020 > 31/01/2020")
            sort_value: Tri (optional, ex: "BOCC_SORT_ASC")
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if id_global_bocc:
            body["idGlobalBocc"] = id_global_bocc
        if interval_publication:
            body["intervalPublication"] = interval_publication
        if sort_value:
            body["sortValue"] = sort_value

        return self.request("/list/bocc", method="POST", body=body)

    def list_bocc_texts(
        self,
        page_number: int = 1,
        page_size: int = 10,
        id_main_bocc: Optional[str] = None,
        idccs: Optional[List[str]] = None,
        interval_publication: Optional[str] = None,
        sort_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des textes d'un BOCC

        POST /list/boccTexts

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            id_main_bocc: ID du BOCC principal (optional)
            idccs: Liste des IDCC (optional)
            interval_publication: Intervalle de publication (optional)
            sort_value: Tri (optional)
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if id_main_bocc:
            body["idMainBocc"] = id_main_bocc
        if idccs:
            body["idccs"] = idccs
        if interval_publication:
            body["intervalPublication"] = interval_publication
        if sort_value:
            body["sortValue"] = sort_value

        return self.request("/list/boccTexts", method="POST", body=body)

    def list_boccs_and_texts(
        self,
        page_number: int = 1,
        page_size: int = 10,
        idcc: Optional[str] = None,
        titre: Optional[str] = None,
        interval_publication: Optional[str] = None,
        sort_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des BOCCs et textes associés

        POST /list/boccsAndTexts

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            idcc: IDCC (optional)
            titre: Titre (optional)
            interval_publication: Intervalle de publication (optional)
            sort_value: Tri (optional)
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if idcc:
            body["idcc"] = idcc
        if titre:
            body["titre"] = titre
        if interval_publication:
            body["intervalPublication"] = interval_publication
        if sort_value:
            body["sortValue"] = sort_value

        return self.request("/list/boccsAndTexts", method="POST", body=body)

    def list_dossiers_legislatifs(
        self,
        legislature_id: int,
        dossier_type: str
    ) -> Dict[str, Any]:
        """
        Liste paginée des dossiers législatifs

        POST /list/dossiersLegislatifs

        Args:
            legislature_id: ID de la législature (REQUIRED)
            dossier_type: Type de dossier législatif (REQUIRED, ex: "LOI_PUBLIEE")
        """
        return self.request(
            "/list/dossiersLegislatifs",
            method="POST",
            body={
                "legislatureId": legislature_id,
                "type": dossier_type
            }
        )

    def list_legislatures(self) -> Dict[str, Any]:
        """
        Liste des législatures

        POST /list/legislatures

        Note: Aucun paramètre requis
        """
        return self.request("/list/legislatures", method="POST", body={})

    def list_questions_ecrites_parlementaires(
        self,
        page_number: int = 1,
        page_size: int = 10,
        parlement_types: Optional[List[str]] = None,
        periode_publication: Optional[str] = None,
        sort_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste paginée des questions écrites parlementaires

        POST /list/questionsEcritesParlementaires

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            parlement_types: Types de parlement (optional, ex: ["AN"])
            periode_publication: Période de publication (optional)
            sort_value: Tri (optional)
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if parlement_types:
            body["parlementTypes"] = parlement_types
        if periode_publication:
            body["periodePublication"] = periode_publication
        if sort_value:
            body["sortValue"] = sort_value

        return self.request(
            "/list/questionsEcritesParlementaires",
            method="POST",
            body=body
        )

    def list_debats_parlementaires(
        self,
        page_number: int = 1,
        page_size: int = 10,
        types_publication: Optional[List[str]] = None,
        date_parution: Optional[str] = None,
        sort_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste paginée des débats parlementaires

        POST /list/debatsParlementaires

        Args:
            page_number: Numéro de page (REQUIRED)
            page_size: Taille de la page (REQUIRED)
            types_publication: Types de publication (optional, ex: ["AN"])
            date_parution: Date de parution (optional)
            sort_value: Tri (optional)
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if types_publication:
            body["typesPublication"] = types_publication
        if date_parution:
            body["dateParution"] = date_parution
        if sort_value:
            body["sortValue"] = sort_value

        return self.request(
            "/list/debatsParlementaires",
            method="POST",
            body=body
        )

    def ping(self) -> Dict[str, Any]:
        """
        Teste le contrôleur de listage

        GET /list/ping
        """
        return self.request("/list/ping", method="GET")
