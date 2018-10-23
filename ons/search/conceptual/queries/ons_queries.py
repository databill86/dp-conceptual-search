"""
This file contains queries for conceptual search
"""
from numpy import ndarray
from elasticsearch_dsl import query as Q

from search.boost_mode import BoostMode

from ons.search.ons_queries import content_query as standard_content_query

from ons.search.fields import AvailableFields, Field
from ons.search.exceptions import MalformedSearchTerm, UnknownSearchVector

from ons.search.queries import FunctionScore
from ons.search.conceptual.queries import VectorScriptScore

from ml.word_embedding.fastText.supervised import SupervisedModel
from ml.word_embedding.utils import clean_string, replace_nouns_with_singulars


def word_vector_keywords_query(search_term: str, num_labels: int, threshold: float, model: SupervisedModel) -> Q.Query:
    """
    Build a bool query to match against generated keyword labels
    :param search_term:
    :param num_labels:
    :param threshold:
    :param model:
    :return:
    """
    # Use the raw keywords field for matching
    field: Field = AvailableFields.KEYWORDS_RAW.value

    # Get predicted labels and their probabilities
    labels, probabilities = model.predict(search_term, k=num_labels, threshold=threshold)

    # Build the individual match queries
    match_queries = [Q.Match(**{field.name: {"query": label}}) for label in labels]
    return Q.Bool(should=match_queries)


def content_query(search_term: str, model: SupervisedModel,
                  field: Field=AvailableFields.EMBEDDING_VECTOR.value,
                  weight: float=1.0,
                  num_labels: int=10,
                  threshold: float=0.1) -> Q.Query:
    """
    Defines the ONS conceptual search content query
    :param search_term:
    :param model:
    :param field:
    :param weight:
    :param num_labels:
    :param threshold:
    :return:
    """
    # First, clean the search term and replace all nouns with singulars
    clean_search_term = replace_nouns_with_singulars(clean_string(search_term))

    if len(clean_search_term) == 0:
        raise MalformedSearchTerm(search_term)

    search_vector: ndarray = model.get_sentence_vector(clean_search_term)
    if search_vector is None:
        raise UnknownSearchVector(search_term)

    # Build function scores
    script_score = VectorScriptScore(field.name, search_vector.tolist(), cosine=True, weight=weight)
    script_score_dict = script_score.to_dict()

    # Generate additional keywords query
    additional_keywords_query = FunctionScore(
        query=word_vector_keywords_query(clean_search_term, num_labels, threshold, model),
        functions=[script_score_dict],
        boost_mode=BoostMode.REPLACE.value
    )

    # Build the original content query
    dis_max_query = standard_content_query(search_term)

    # Combine as DisMax with FunctionScore
    query = Q.DisMax(
        queries=[dis_max_query, additional_keywords_query]
    )

    return FunctionScore(
        query=query,
        functions=[script_score_dict],
        boost_mode=BoostMode.AVG.value
    )
