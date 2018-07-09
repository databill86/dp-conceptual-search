from elasticsearch_dsl import query as Q

from enum import Enum
from numpy import ndarray

from ons.search import fields
from core.word_embedding.models.supervised import SupervisedModel


class RescoreQuery(Q.Query):
    name = "rescore"


class ScriptScore(Q.Query):
    name = "script_score"


class FunctionScore(Q.Query):
    name = "function_score"


class Scripts(Enum):
    BINARY_VECTOR_SCORE = "binary_vector_score"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class ScriptLanguage(Enum):
    KNN = "knn"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class BoostMode(Enum):
    REPLACE = "replace"
    MULTIPLY = "multiply"
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


def vector_script_score(
        field: fields.Field,
        vector: ndarray,
        weight: float=1.0) -> Q.Query:
    params = {
        "cosine": True,
        "field": field.name,
        "vector": vector.tolist()
    }
    script_score = {
        "lang": ScriptLanguage.KNN.value,
        "params": params,
        "script": Scripts.BINARY_VECTOR_SCORE.value
    }

    if weight > 1:
        script_score['weight'] = weight

    # return script_score
    return ScriptScore(**script_score)


def date_decay_function() -> Q.Query:
    q = Q.SF('linear', **{fields.releaseDate.name: {
        "origin": "now",
        "scale": "365d",
        "offset": "30d",
        "decay": 0.5
    }})
    return q


def word_vector_keywords_query(
        search_term: str,
        model: SupervisedModel,
        k: int=10,
        threshold: float=0.1) -> Q.Query:
    """
    TODO - (Re)Index normalised vectors
    :param search_term:
    :param model:
    :param k:
    :param threshold:
    :return:
    """
    labels, probabilities = model.predict(
        search_term, k=k, threshold=threshold)

    match_queries = []
    for label, probability in zip(labels, probabilities):
        match_queries.append(Q.Match(
            **{fields.keywords.name: {"query": label.replace("_", " "), "boost": probability}}))

    # query = Q.DisMax(queries=match_queries)
    query = Q.Bool(should=match_queries)
    return query


def user_rescore_query(
        user_vector: ndarray,
        score_mode: BoostMode=BoostMode.AVG,
        window_size: int=100,
        query_weight: float=0.5,
        rescore_query_weight: float=1.2) -> RescoreQuery:
    """
    Generates a rescore query from a users session vector
    :param user_vector:
    :param score_mode:
    :param window_size:
    :param query_weight:
    :param rescore_query_weight:
    :return:
    """
    user_script_score = vector_script_score(
        fields.embedding_vector, user_vector)

    rescore = {
        "window_size": window_size,
        "query": {
            "score_mode": score_mode.value,
            "rescore_query": {
                "function_score": user_script_score.to_dict()
            },
            "query_weight": query_weight,
            "rescore_query_weight": rescore_query_weight
        }
    }

    return RescoreQuery(**rescore)


def content_query(
        search_term: str,
        model: SupervisedModel,
        boost_mode: BoostMode=BoostMode.AVG,
        min_score: float=0.01,
        **kwargs) -> Q.Query:
    """
    Conceptual search (main) content query.
    Requires embedding_vectors to be indexed in Elasticsearch.
    :param search_term:
    :param model:
    :param boost_mode:
    :param min_score:
    :return:
    """
    from ons.search.filter_functions import content_filter_functions
    from ons.search.queries import content_query as ons_content_query
    from ons.search.queries import function_score_content_query

    search_vector = model.get_sentence_vector(search_term)

    # Build the original ONS content query
    dis_max_query = ons_content_query(search_term)
    should = [dis_max_query]

    # Try to build additional keywords query
    try:
        terms_query = word_vector_keywords_query(
            search_term, model)
        should.append(terms_query)
    except ValueError as e:
        # Log the error but continue with the query (we can still return results, just can't
        # auto generate keywords for matching.
        # Note the script score will still facilitate non-keyword matching.
        from sanic.log import logger
        logger.warning("Caught exception while generating model keywords: %s", str(e), exc_info=1)

    # Build function scores
    script_score = vector_script_score(fields.embedding_vector, search_vector)
    date_function = date_decay_function()

    function_scores = [script_score.to_dict(), date_function.to_dict()]
    # function_scores = [script_score.to_dict()]

    additional_function_scores = kwargs.get(
        "function_scores", content_filter_functions())

    if additional_function_scores is not None:
        if hasattr(additional_function_scores, "__iter__") is False:
            additional_function_scores = [additional_function_scores]
        function_scores.extend(additional_function_scores)

    function_score = FunctionScore(
        query=Q.Bool(should=should),
        min_score=min_score,
        boost_mode=boost_mode.value,
        functions=function_scores)

    return Q.DisMax(queries=[function_score_content_query(dis_max_query, content_filter_functions()), function_score])
