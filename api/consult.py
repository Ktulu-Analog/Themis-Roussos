"""
Module Consult Controller
Gère tous les endpoints de consultation de textes de l'API Légifrance
39 endpoints disponibles
"""

from typing import Dict, Any, Optional, List
from .base import BaseAPI


class ConsultController(BaseAPI):
    """
    Contrôleur de consultation des textes juridiques
    Permet d'accéder au contenu des codes, lois, décrets, jurisprudence, etc.
    """

    # ========== CODES ==========

    def get_code(self, text_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Contenu d'un code

        POST /consult/code

        Args:
            text_id: ID du code (ex: LEGITEXT000006070721 pour Code civil)
            date: Date de version (YYYY-MM-DD). Si None, utilise la date du jour

        Returns:
            Contenu complet du code avec ses sections
        """
        import datetime
        if date is None:
            date = datetime.date.today().isoformat()

        return self.request(
            "/consult/code",
            method="POST",
            body={"textId": text_id, "date": date}
        )

    def get_code_with_ancien_id(self, ancien_id: str) -> Dict[str, Any]:
        """
        Contenu d'un code par son ancien ID

        POST /consult/getCodeWithAncienId
        """
        return self.request(
            "/consult/getCodeWithAncienId",
            method="POST",
            body={"ancienId": ancien_id}
        )

    def get_code_table_matieres(
        self,
        text_id: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Table des matières d'un code (déprécié, utiliser legi_table_matieres)

        POST /consult/code/tableMatieres

        Note: Même schema que /consult/code - date requise
        """
        import datetime
        if date is None:
            date = datetime.date.today().isoformat()

        return self.request(
            "/consult/code/tableMatieres",
            method="POST",
            body={"textId": text_id, "date": date}
        )

    # ========== ARTICLES ==========

    def get_article(self, article_id: str) -> Dict[str, Any]:
        """
        Contenu d'un article

        POST /consult/getArticle

        Args:
            article_id: ID de l'article (REQUIRED)
        """
        return self.request(
            "/consult/getArticle",
            method="POST",
            body={"id": article_id}
        )

    def get_article_with_id_eli_or_alias(self, id_eli_or_alias: str) -> Dict[str, Any]:
        """
        Contenu d'un article par ID ELI ou alias

        POST /consult/getArticleWithIdEliOrAlias

        Args:
            id_eli_or_alias: ID ELI ou alias (REQUIRED)
                           (ex: "/eli/decret/2021/7/13/PRMD2117108D/jo/article_1")
        """
        return self.request(
            "/consult/getArticleWithIdEliOrAlias",
            method="POST",
            body={"idEliOrAlias": id_eli_or_alias}
        )

    def get_article_with_id_and_num(
        self,
        text_id: str,
        article_num: str
    ) -> Dict[str, Any]:
        """
        Contenu d'un article par ID de texte et numéro d'article

        POST /consult/getArticleWithIdAndNum

        Args:
            text_id: ID du texte (id)
            article_num: Numéro d'article (num)
        """
        return self.request(
            "/consult/getArticleWithIdAndNum",
            method="POST",
            body={"id": text_id, "num": article_num}
        )

    def get_article_by_cid(self, cid: str) -> Dict[str, Any]:
        """
        Contenu des versions d'un article par CID

        POST /consult/getArticleByCid

        Args:
            cid: CID de l'article (REQUIRED)
        """
        return self.request(
            "/consult/getArticleByCid",
            method="POST",
            body={"cid": cid}
        )

    def get_same_num_article(
        self,
        article_cid: str,
        article_num: str,
        text_cid: str,
        date: str
    ) -> Dict[str, Any]:
        """
        Liste des articles ayant eu le même numéro

        POST /consult/sameNumArticle

        Args:
            article_cid: CID de l'article (REQUIRED)
            article_num: Numéro de l'article (REQUIRED)
            text_cid: CID du texte (REQUIRED)
            date: Date de référence (REQUIRED, format YYYY-MM-DD)
        """
        return self.request(
            "/consult/sameNumArticle",
            method="POST",
            body={
                "articleCid": article_cid,
                "articleNum": article_num,
                "textCid": text_cid,
                "date": date
            }
        )

    # ========== LIENS D'ARTICLES ==========

    def get_concordance_links_article(self, article_id: str) -> Dict[str, Any]:
        """
        Liste des liens de concordance d'un article

        POST /consult/concordanceLinksArticle

        Args:
            article_id: ID de l'article (REQUIRED, nom du param: articleId)
        """
        return self.request(
            "/consult/concordanceLinksArticle",
            method="POST",
            body={"articleId": article_id}
        )

    def get_related_links_article(self, article_id: str) -> Dict[str, Any]:
        """
        Liste des liens relatifs d'un article

        POST /consult/relatedLinksArticle

        Args:
            article_id: ID de l'article (REQUIRED, nom du param: articleId)
        """
        return self.request(
            "/consult/relatedLinksArticle",
            method="POST",
            body={"articleId": article_id}
        )

    def get_service_public_links_article(
        self,
        article_cid: Optional[str] = None,
        fond: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Liste des liens service-public d'un article

        POST /consult/servicePublicLinksArticle

        Args:
            article_cid: CID de l'article (optional)
            fond: Fond de consultation (optional, ex: "JORF")
        """
        body = {}
        if article_cid:
            body["articleCid"] = article_cid
        if fond:
            body["fond"] = fond
        return self.request(
            "/consult/servicePublicLinksArticle",
            method="POST",
            body=body
        )

    def has_service_public_links_article(self, article_ids: List[str]) -> Dict[str, Any]:
        """
        Liste d'articles possédant des liens service-public

        POST /consult/hasServicePublicLinksArticle

        Note: Schema non défini dans l'API - utilise ids en array
        """
        return self.request(
            "/consult/hasServicePublicLinksArticle",
            method="POST",
            body={"ids": article_ids}
        )

    # ========== JOURNAL OFFICIEL (JORF) ==========

    def get_jorf(self, text_cid: str) -> Dict[str, Any]:
        """
        Contenu d'un texte du Journal Officiel

        POST /consult/jorf

        Args:
            text_cid: CID du texte (REQUIRED, nom du param: textCid)
        """
        return self.request(
            "/consult/jorf",
            method="POST",
            body={"textCid": text_cid}
        )

    def get_jorf_cont(
        self,
        jorf_id: Optional[str] = None,
        num: Optional[str] = None,
        date: Optional[str] = None,
        search_text: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Liste du sommaire JORF

        POST /consult/jorfCont

        Args:
            jorf_id: ID du conteneur JORF (optional)
            num: Numéro de JORF (optional)
            date: Date de référence (optional)
            search_text: Texte à rechercher (optional)
            page_number: Numéro de page (optional, default=1)
            page_size: Taille de page (optional, default=10)
        """
        body = {
            "pageNumber": page_number,
            "pageSize": page_size
        }
        if jorf_id:
            body["id"] = jorf_id
        if num:
            body["num"] = num
        if date:
            body["date"] = date
        if search_text:
            body["searchText"] = search_text

        return self.request(
            "/consult/jorfCont",
            method="POST",
            body=body
        )

    def get_jorf_part(self, text_cid: str) -> Dict[str, Any]:
        """
        Contenu texte fonds JORF

        POST /consult/jorfPart

        Args:
            text_cid: CID du texte (REQUIRED, nom du param: textCid)
        """
        return self.request(
            "/consult/jorfPart",
            method="POST",
            body={"textCid": text_cid}
        )

    def get_jo_with_nor(self, nor: str) -> Dict[str, Any]:
        """
        Contenu d'un JO par son numéro NOR

        POST /consult/getJoWithNor

        Args:
            nor: Numéro NOR (REQUIRED)
        """
        return self.request(
            "/consult/getJoWithNor",
            method="POST",
            body={"nor": nor}
        )

    def get_last_n_jo(self, nb_element: int = 10) -> Dict[str, Any]:
        """
        Derniers journaux officiels

        POST /consult/lastNJo

        Args:
            nb_element: Nombre de JO à remonter (REQUIRED)
        """
        return self.request(
            "/consult/lastNJo",
            method="POST",
            body={"nbElement": nb_element}
        )

    def eli_and_alias_redirection_texte(self, id_eli_or_alias: str) -> Dict[str, Any]:
        """
        Contenu des textes du JO par ELI ou alias

        POST /consult/eliAndAliasRedirectionTexte

        Args:
            id_eli_or_alias: ID ELI ou alias (REQUIRED, nom du param: idEliOrAlias)
        """
        return self.request(
            "/consult/eliAndAliasRedirectionTexte",
            method="POST",
            body={"idEliOrAlias": id_eli_or_alias}
        )

    # ========== CONVENTIONS COLLECTIVES (KALI) ==========

    def get_kali_article(self, article_id: str) -> Dict[str, Any]:
        """
        Contenu des conventions collectives depuis un article

        POST /consult/kaliArticle

        Args:
            article_id: ID de l'article (REQUIRED)
        """
        return self.request(
            "/consult/kaliArticle",
            method="POST",
            body={"id": article_id}
        )

    def get_kali_cont(self, cont_id: str) -> Dict[str, Any]:
        """
        Contenu des conteneurs des conventions collectives

        POST /consult/kaliCont

        Args:
            cont_id: ID du conteneur (REQUIRED)
        """
        return self.request(
            "/consult/kaliCont",
            method="POST",
            body={"id": cont_id}
        )

    def get_kali_cont_idcc(self, idcc: str) -> Dict[str, Any]:
        """
        Contenu des conteneurs des conventions collectives par IDCC

        POST /consult/kaliContIdcc

        Args:
            idcc: Numéro IDCC (REQUIRED)
        """
        return self.request(
            "/consult/kaliContIdcc",
            method="POST",
            body={"id": idcc}
        )

    def get_kali_section(self, section_id: str) -> Dict[str, Any]:
        """
        Contenu des conventions collectives depuis une section

        POST /consult/kaliSection

        Args:
            section_id: ID de la section (REQUIRED)
        """
        return self.request(
            "/consult/kaliSection",
            method="POST",
            body={"id": section_id}
        )

    def get_kali_text(self, text_id: str) -> Dict[str, Any]:
        """
        Contenu d'une convention collective

        POST /consult/kaliText

        Args:
            text_id: ID du texte (REQUIRED)
        """
        return self.request(
            "/consult/kaliText",
            method="POST",
            body={"id": text_id}
        )

    # ========== JURISPRUDENCE (JURI) ==========

    def get_juri(self, text_id: str) -> Dict[str, Any]:
        """
        Contenu texte fonds JURI (jurisprudence)

        POST /consult/juri

        Args:
            text_id: ID du texte (REQUIRED)
        """
        return self.request(
            "/consult/juri",
            method="POST",
            body={"textId": text_id}
        )

    def get_juri_plan_classement(
        self,
        juri_id: Optional[str] = None,
        libelle: Optional[str] = None,
        niveau: Optional[int] = None,
        page: Optional[int] = None,
        fond: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Contenu texte fonds JURI avec plan de classement

        POST /consult/getJuriPlanClassement

        Args:
            juri_id: ID du JURINOME (optional)
            libelle: Libellé recherché (optional)
            niveau: Niveau (optional)
            page: Numéro de page (optional)
            fond: Fond à rechercher (optional, ex: "juri")
        """
        body = {}
        if juri_id:
            body["id"] = juri_id
        if libelle:
            body["libelle"] = libelle
        if niveau is not None:
            body["niveau"] = niveau
        if page is not None:
            body["page"] = page
        if fond:
            body["fond"] = fond

        return self.request(
            "/consult/getJuriPlanClassement",
            method="POST",
            body=body
        )

    def get_juri_with_ancien_id(self, ancien_id: str) -> Dict[str, Any]:
        """
        Contenu d'un texte juri par ancien ID

        POST /consult/getJuriWithAncienId
        """
        return self.request(
            "/consult/getJuriWithAncienId",
            method="POST",
            body={"ancienId": ancien_id}
        )

    # ========== AUTRES FONDS ==========

    def get_cnil(self, text_id: str) -> Dict[str, Any]:
        """
        Contenu texte fonds CNIL

        POST /consult/cnil

        Args:
            text_id: ID du texte (REQUIRED)
        """
        return self.request(
            "/consult/cnil",
            method="POST",
            body={"textId": text_id}
        )

    def get_cnil_with_ancien_id(self, ancien_id: str) -> Dict[str, Any]:
        """
        Contenu d'un texte CNIL par ancien ID

        POST /consult/getCnilWithAncienId
        """
        return self.request(
            "/consult/getCnilWithAncienId",
            method="POST",
            body={"ancienId": ancien_id}
        )

    def get_law_decree(self, text_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Contenu texte type LODA (lois et décrets autonomes)

        POST /consult/lawDecree

        Args:
            text_id: ID du texte (REQUIRED)
            date: Date de consultation (REQUIRED). Si None, utilise la date du jour
        """
        import datetime
        if date is None:
            date = datetime.date.today().isoformat()

        return self.request(
            "/consult/lawDecree",
            method="POST",
            body={"textId": text_id, "date": date}
        )

    def get_legi_part(self, text_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Contenu texte fonds LEGI

        POST /consult/legiPart

        Args:
            text_id: ID du texte (REQUIRED)
            date: Date de consultation (REQUIRED). Si None, utilise la date du jour
        """
        import datetime
        if date is None:
            date = datetime.date.today().isoformat()

        return self.request(
            "/consult/legiPart",
            method="POST",
            body={"textId": text_id, "date": date}
        )

    def get_acco(self, acco_id: str) -> Dict[str, Any]:
        """
        Contenu d'un accord d'entreprise

        POST /consult/acco

        Args:
            acco_id: ID de l'accord (REQUIRED)
        """
        return self.request(
            "/consult/acco",
            method="POST",
            body={"id": acco_id}
        )

    def get_circulaire(self, circulaire_id: str) -> Dict[str, Any]:
        """
        Contenu d'une circulaire

        POST /consult/circulaire

        Args:
            circulaire_id: ID de la circulaire (REQUIRED)
        """
        return self.request(
            "/consult/circulaire",
            method="POST",
            body={"id": circulaire_id}
        )

    def get_debat(self, debat_id: str) -> Dict[str, Any]:
        """
        Contenu d'un débat parlementaire

        POST /consult/debat

        Args:
            debat_id: ID du débat (REQUIRED)
        """
        return self.request(
            "/consult/debat",
            method="POST",
            body={"id": debat_id}
        )

    def get_dossier_legislatif(self, dossier_id: str) -> Dict[str, Any]:
        """
        Contenu d'un dossier législatif

        POST /consult/dossierLegislatif

        Args:
            dossier_id: ID du dossier (REQUIRED)
        """
        return self.request(
            "/consult/dossierLegislatif",
            method="POST",
            body={"id": dossier_id}
        )

    # ========== SECTIONS ET TABLES ==========

    def get_section_by_cid(self, cid: str) -> Dict[str, Any]:
        """
        Contenu d'une section

        POST /consult/getSectionByCid

        Args:
            cid: CID de la section (REQUIRED)
        """
        return self.request(
            "/consult/getSectionByCid",
            method="POST",
            body={"cid": cid}
        )

    def get_tables(self, end_year: int, start_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Liste des tables annuelles

        POST /consult/getTables

        Args:
            end_year: Année de fin (REQUIRED)
            start_year: Année de début (optional)
        """
        body = {"endYear": end_year}
        if start_year is not None:
            body["startYear"] = start_year

        return self.request(
            "/consult/getTables",
            method="POST",
            body=body
        )

    def get_legi_table_matieres(
        self,
        text_id: str,
        date: Optional[str] = None,
        nature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Table des matières d'un texte LODA ou CODE

        POST /consult/legi/tableMatieres

        Args:
            text_id: ID du texte (REQUIRED)
            date: Date de consultation (REQUIRED). Si None, utilise la date du jour
            nature: Nature du texte (optional, ex: "CODE", "DECRET")
        """
        import datetime
        if date is None:
            date = datetime.date.today().isoformat()

        body = {"textId": text_id, "date": date}
        if nature:
            body["nature"] = nature

        return self.request(
            "/consult/legi/tableMatieres",
            method="POST",
            body=body
        )

    # ========== MÉTADONNÉES ==========

    def get_bocc_text_pdf_metadata(
        self,
        bocc_id: Optional[str] = None,
        for_global_bocc: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Métadonnées d'un PDF lié à un texte unitaire BOCC

        POST /consult/getBoccTextPdfMetadata

        Args:
            bocc_id: ID du BOCC (optional)
            for_global_bocc: Pour BOCC global (optional)
        """
        body = {}
        if bocc_id:
            body["id"] = bocc_id
        if for_global_bocc is not None:
            body["forGlobalBocc"] = for_global_bocc

        return self.request(
            "/consult/getBoccTextPdfMetadata",
            method="POST",
            body=body
        )

    # ========== PING ==========

    def ping(self) -> Dict[str, Any]:
        """
        Teste le contrôleur de consultation

        GET /consult/ping
        """
        return self.request("/consult/ping", method="GET")
