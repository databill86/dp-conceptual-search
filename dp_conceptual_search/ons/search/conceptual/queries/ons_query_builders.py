"""
This file contains queries for conceptual search
"""
import logging

from numpy import ndarray
from elasticsearch_dsl import query as Q

from dp_conceptual_search.search.boost_mode import BoostMode
from dp_conceptual_search.ons.search.queries import ons_query_builders
from dp_conceptual_search.search.dsl.function_score import FunctionScore
from dp_conceptual_search.ons.search.fields import AvailableFields, Field
from dp_conceptual_search.search.dsl.vector_script_score import VectorScriptScore
from dp_conceptual_search.ons.search.exceptions import MalformedSearchTerm, UnknownSearchVector
from dp_conceptual_search.ons.search.conceptual.client.fasttext_client import get_fasttext_client

from dp_fasttext.client import Client
from dp_fasttext.ml.utils import clean_string, replace_nouns_with_singulars


async def word_vector_keywords_query(search_term: str, num_labels: int, threshold: float, client: Client,
                                     headers: dict = None) -> Q.Query:
    """
    Build a bool query to match against generated keyword labels
    :param search_term:
    :param num_labels:
    :param threshold:
    :param client:
    :param headers:
    :return:
    """
    # Use the raw keywords field for matching
    field: Field = AvailableFields.KEYWORDS_RAW.value

    # Get predicted labels and their probabilities
    labels, probabilities = await client.predict(search_term, num_labels, threshold, headers=headers)

    logging.debug("Generated additional keywords", extra={
        "search_term": search_term,
        "keywords": labels
    })

    # Build the individual match queries
    match_queries = [Q.Match(**{field.name: {"query": label}}) for label in labels]
    return Q.Bool(should=match_queries)


async def build_content_query(search_term: str,
                              context: str,
                              field: Field = AvailableFields.EMBEDDING_VECTOR.value,
                              num_labels: int = 10,
                              threshold: float = 0.1) -> Q.Query:
    """
    Defines the ONS conceptual search content query
    :param search_term:
    :param context:
    :param field:
    :param num_labels:
    :param threshold:
    :return:
    """
    # Initialise dp-fastText client
    client: Client
    async with get_fasttext_client() as client:
        logging.info("Using client", extra={
            "client": client
        })
        # First, clean the search term and replace all nouns with singulars
        clean_search_term = replace_nouns_with_singulars(clean_string(search_term))

        if len(clean_search_term) == 0:
            raise MalformedSearchTerm(search_term)

        # Set request context
        headers = {Client.REQUEST_ID_HEADER: context}

        wv_keywords_query = word_vector_keywords_query(clean_search_term, num_labels, threshold, client, headers)

        search_vector: ndarray = await client.get_sentence_vector(clean_search_term, headers=headers)
        if search_vector is None:
            raise UnknownSearchVector(search_term)

        # Build function scores
        script_score = VectorScriptScore(field.name, search_vector, cosine=True)
        script_score_dict = script_score.to_dict()

        # Generate additional keywords query
        additional_keywords_query = FunctionScore(
            query=await wv_keywords_query,
            functions=[script_score_dict],
            boost_mode=BoostMode.REPLACE.value
        )

        # Build the original content query
        dis_max_query = ons_query_builders.build_content_query(search_term)

        # Combine as DisMax with FunctionScore
        query = Q.DisMax(
            queries=[dis_max_query, additional_keywords_query]
        )

        return FunctionScore(
            query=query,
            functions=[script_score_dict],
            boost_mode=BoostMode.AVG.value
        )
