"""
Tests our UnsupervisedModel class
"""
from unittest import TestCase

from dp_conceptual_search.config import CONFIG
from dp_conceptual_search.ml.word_embedding.fastText.unsupervised import UnsupervisedModel


class SupervisedModelTestCase(TestCase):
    def setUp(self):
        """
        Initialise the default model
        :return:
        """
        self.model = UnsupervisedModel(CONFIG.ML.unsupervised_model_filename)

    def test_similar_by_word(self):
        """
        Tests the similar_by_word method
        :return:
        """
        word = "homicide"
        topn = 10

        similar_words = self.model.similar_by_word(word, top_n=topn, return_similarity=True)

        self.assertIsNotNone(similar_words, "similar_words should not be none")
        self.assertEqual(len(similar_words), topn, "expected {topn} results, got {actual}"
                         .format(topn=topn, actual=len(similar_words)))

        # Assert each element has a word and a score
        for similar_word, similar_score in similar_words:
            self.assertIsNotNone(similar_word, "similar_word should not be none")
            self.assertIsNotNone(similar_score, "similar_score should not be none")

            self.assertIsInstance(similar_word, str, "similar_word should be instance of string")
            self.assertIsInstance(similar_score, float, "similar_score should be instance of float")

            self.assertGreater(similar_score, 0, "similar_score should be greater than zero")

    def test_similar_by_vector(self):
        """
        Tests the similar_by_vector method
        :return:
        """
        word = "homicide"
        word_vector = self.model.word_vec(word, use_norm=False)
        topn = 10

        similar_words = self.model.similar_by_vector(word_vector, top_n=topn, return_similarity=True)

        self.assertIsNotNone(similar_words, "similar_words should not be none")
        self.assertEqual(len(similar_words), topn, "expected {topn} results, got {actual}"
                         .format(topn=topn, actual=len(similar_words)))

        # Assert each element has a word and a score
        for similar_word, similar_score in similar_words:
            self.assertIsNotNone(similar_word, "similar_word should not be none")
            self.assertIsNotNone(similar_score, "similar_score should not be none")

            self.assertIsInstance(similar_word, str, "similar_word should be instance of string")
            self.assertIsInstance(similar_score, float, "similar_score should be instance of float")

            self.assertGreater(similar_score, 0, "similar_score should be greater than zero")