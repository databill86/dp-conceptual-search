from server.search.search_engine import SearchEngine


class ConceptualSearchEngine(SearchEngine):
    from server.word_embedding.sanic_supervised_models import load_model
    from server.word_embedding.models.supervised import SupervisedModels, SupervisedModel

    word_embedding_model: SupervisedModel = load_model(SupervisedModels.ONS)

    def __init__(self, **kwargs):
        super(ConceptualSearchEngine, self).__init__(**kwargs)

    def content_query(
            self,
            search_term: str,
            current_page: int = 1,
            size: int = 10,
            **kwargs):
        """
        Overwrite SearchEngine content query to use a vector rescore.
        :param search_term:
        :param current_page:
        :param size:
        :param kwargs:
        :return:
        """
        from server.search.fields import embedding_vector
        from server.search.sort_by import SortFields
        from server.search.conceptual_search.conceptual_search_queries import content_query

        from numpy import ndarray

        kwargs_copy = kwargs.copy()
        sort_by = kwargs_copy.pop("sort_by", SortFields.relevance)

        if sort_by == SortFields.relevance:
            # Build the content query with vector function score
            query = content_query(
                search_term,
                ConceptualSearchEngine.word_embedding_model,
                **kwargs_copy)

            # Prepare the final query and omit the embedding_vector field from
            # _source
            query_dict = {
                "query": query.to_dict()
            }

            # If user_vector is specified, add a user vector function score
            if 'user_vector' in kwargs:
                from server.search.conceptual_search.conceptual_search_queries import user_rescore_query
                user_vector: ndarray = kwargs.get('user_vector')

                if user_vector is not None and isinstance(
                        user_vector, ndarray):

                    query_dict["rescore"] = user_rescore_query(user_vector)

            s = self.build_query(
                query_dict,
                search_term=search_term,
                current_page=current_page,
                size=size,
                **kwargs_copy)

            # Exclude embedding vector for source
            s = s.source(exclude=[embedding_vector.name])

            return s
        else:
            return super(
                ConceptualSearchEngine,
                self).content_query(
                search_term,
                current_page=current_page,
                size=size,
                **kwargs)

    def featured_result_query(self, search_term):
        """
        Builds and executes the standard ONS featured result query (from babbage)
        :param search_term:
        :return:
        """
        from server.search.content_types import home_page_census, product_page

        type_filters = [product_page.name, home_page_census.name]

        s = super(ConceptualSearchEngine,
                  self).content_query(
            search_term,
            function_scores=None,
            type_filters=type_filters,
            size=1)
        return s
