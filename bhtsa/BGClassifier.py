import nltk
from nltk.util import ngrams
import numpy as np
import pickle
from process_twt import *


class BGClassifier(object):
    """
    A Naive Bayes Classifier for sentiment analysis

    Attributes:
        feature_list: A list containing informative words
        stop_words: A list containing stop words
        is_trained: An indicator of whether classifier is trained
        NBClassifier: Classifier
    """

    def __init__(self, name='BGClassifier', n=2):
        self.feature_list = []
        self.stop_words = get_stopwords()
        self.is_trained = False
        self.BGClassifier = []
        self.ngram = n
        self.name = name

    def get_feature_vector(self, twt):
        feature_vector = []
        # split tweet into words
        words = twt.split()
        for w in words:
            # strip punctuation
            w = w.strip('\'"?,.')
            # check if the word stats with an alphabet
            val = re.search(r"^[a-zA-Z][a-zA-Z0-9]*$", w)
            # ignore if it is a stop word
            if w in self.stop_words or val is None:
                continue
            else:
                feature_vector.append(w.lower())
        feature_vector = ngrams(feature_vector, self.ngram)
        return list(feature_vector)                 # feature_vector should be list instead of generator

    def extract_features(self, twt):
        # twt = ngrams(twt, self.ngram)
        twt_words = set(twt)
        features = {}
        for word in self.feature_list:
            features['contains(%s)' % ' '.join(word)] = (word in twt_words)
        return features

    def train(self, pos_twt, neg_twt):
        tweets = []
        for row in pos_twt:
            sentiment = 'positive'
            processed_twt = preprocess(row)
            feature_vector = self.get_feature_vector(processed_twt)
            self.feature_list.extend(feature_vector)
            tweets.append((feature_vector, sentiment))
        for row in neg_twt:
            sentiment = 'negative'
            processed_twt = preprocess(row)
            feature_vector = self.get_feature_vector(processed_twt)
            self.feature_list.extend(feature_vector)
            tweets.append((feature_vector, sentiment))
        # remove duplicates in feature list
        self.feature_list = list(set(self.feature_list))

        # train classifier
        training_set = nltk.classify.util.apply_features(self.extract_features, tweets)
        self.BGClassifier = nltk.NaiveBayesClassifier.train(training_set)
        self.is_trained = True

    def test(self, twt):
        if self.is_trained:
            score = np.zeros((len(twt), 1))
            for cnt, row in enumerate(twt):
                row = preprocess(row)
                score[cnt] = (self.BGClassifier.prob_classify(self.extract_features(
                    self.get_feature_vector(row)))).prob('positive')
            return score

    def informative_features(self, num=10):
        if self.is_trained:
            return self.BGClassifier.show_most_informative_features(num)
        else:
            return ['Error: Classifier has not been trained']

    def save(self):
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'model')
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(os.path.join(path, self.name+'.pickle'), 'wb')
        pickle.dump(self, f)
        f.close()