#! /usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
from nltk.corpus import stopwords
from feature import Feature
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
import numpy as np
import math
from utils import LogUtil


class WordMatchShare(object):
    """
    提取<Q1,Q2>特征: word_match_share
    """

    stops = set(stopwords.words("english"))

    @staticmethod
    def word_match_share(row):
        """
        针对一行抽取特征
        :param row: DataFrame中的一行数据
        :return: 特征值
        """
        q1words = {}
        q2words = {}
        for word in str(row['question1']).lower().split():
            if word not in WordMatchShare.stops:
                q1words[word] = 1
        for word in str(row['question2']).lower().split():
            if word not in WordMatchShare.stops:
                q2words[word] = 1
        if len(q1words) == 0 or len(q2words) == 0:
            # The computer-generated chaff includes a few questions that are nothing but stopwords
            return [0.]
        shared_words_in_q1 = [w for w in q1words.keys() if w in q2words]
        shared_words_in_q2 = [w for w in q2words.keys() if w in q1words]
        R = 1.0 * (len(shared_words_in_q1) + len(shared_words_in_q2)) / (len(q1words) + len(q2words))
        return [R]

    @staticmethod
    def run(train_df, test_df, feature_pt):
        """
        抽取train.csv test.csv特征
        :param train_df: train.csv数据
        :param test_df: test.csv数据
        :param feature_pt: 特征文件路径
        :return: None
        """
        train_features = train_df.apply(WordMatchShare.word_match_share, axis=1, raw=True)
        Feature.save_dataframe(train_features, feature_pt + '/word_match_share.train.smat')

        test_features = test_df.apply(WordMatchShare.word_match_share, axis=1, raw=True)
        Feature.save_dataframe(test_features, feature_pt + '/word_match_share.test.smat')

        word_match_share = train_features.apply(lambda x: x[0])
        plt.figure(figsize=(15, 5))
        plt.hist(word_match_share[train_df['is_duplicate'] == 0], bins=20, normed=True, label='Not Duplicate')
        plt.hist(word_match_share[train_df['is_duplicate'] == 1], bins=20, normed=True, alpha=0.7, label='Duplicate')
        plt.legend()
        plt.title('Label distribution over word_match_share', fontsize=15)
        plt.xlabel('word_match_share', fontsize=15)
        plt.show()

        return

    @staticmethod
    def demo():
        """
        使用样例
        :return: NONE
        """
        # 读取配置文件
        cf = ConfigParser.ConfigParser()
        cf.read("../conf/python.conf")

        # 加载train.csv文件
        train_data = pd.read_csv('%s/train.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 加载test.csv文件
        test_data = pd.read_csv('%s/test.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 特征文件路径
        feature_path = cf.get('DEFAULT', 'feature_question_pair_pt')
        # 提取特征
        WordMatchShare.run(train_data, test_data, feature_path)


class TFIDFWordMatchShare(object):
    """
    基于TF-IDF的词共享特征
    """

    stops = set(stopwords.words("english"))
    weights = {}

    @staticmethod
    def cal_weight(count, eps=10000, min_count=2):
        """
        根据词语出现次数计算权重
        :param count: 词语出现次数
        :param eps: 平滑常数
        :param min_count: 最少出现次数
        :return: 权重
        """
        if count < min_count:
            return 0.
        else:
            return 1. / (count + eps)

    @staticmethod
    def get_weights(data):
        """
        获取weight字典
        :param data: 数据集，一般是train.csv
        :return: None
        """
        qs_data = pd.Series(data['question1'].tolist() + data['question2'].tolist()).astype(str)
        words = (" ".join(qs_data)).lower().split()
        counts = Counter(words)
        TFIDFWordMatchShare.weights = {word: TFIDFWordMatchShare.cal_weight(count) for word, count in counts.items()}

    @staticmethod
    def tfidf_word_match_share(row):
        """
        针对一个<Q1,Q2>抽取特征
        :param row: 一个<Q1,Q2>实例
        :return: 特征值
        """
        q1words = {}
        q2words = {}
        for word in str(row['question1']).lower().split():
            if word not in TFIDWordMatchShare.stops:
                q1words[word] = 1
        for word in str(row['question2']).lower().split():
            if word not in TFIDWordMatchShare.stops:
                q2words[word] = 1
        if len(q1words) == 0 or len(q2words) == 0:
            # The computer-generated chaff includes a few questions that are nothing but stopwords
            return [0.]

        shared_weights = [TFIDFWordMatchShare.weights.get(w, 0) for w in q1words.keys() if w in q2words] + [TFIDWordMatchShare.weights.get(w, 0) for w in                                                                                q2words.keys() if w in q1words]
        total_weights = [TFIDFWordMatchShare.weights.get(w, 0) for w in q1words] + [TFIDWordMatchShare.weights.get(w, 0) for w in q2words]
        if 1e-6 > np.sum(total_weights):
            return [0.]
        R = np.sum(shared_weights) / np.sum(total_weights)
        return [R]

    @staticmethod
    def run(train_df, test_df, feature_pt):
        """
        抽取train.csv和test.csv的<Q1,Q2>特征：tfidf_word_match_share
        :param train_df: train.csv
        :param test_df: test.csv
        :param feature_pt: 特征文件目录
        :return: None
        """
        # 获取weights信息
        TFIDWordMatchShare.get_weights(train_data)
        # 抽取特征
        train_features = train_df.apply(TFIDWordMatchShare.tfidf_word_match_share, axis=1, raw=True)
        Feature.save_dataframe(train_features, feature_pt + '/tfidf_word_match_share.train.smat')
        test_features = test_df.apply(TFIDWordMatchShare.tfidf_word_match_share, axis=1, raw=True)
        Feature.save_dataframe(test_features, feature_pt + '/tfidf_word_match_share.test.smat')
        # 绘图
        tfidf_word_match_share = train_features.apply(lambda x: x[0])
        plt.figure(figsize=(15, 5))
        plt.hist(tfidf_word_match_share[train_df['is_duplicate'] == 0].fillna(0), bins=20, normed=True,
                 label='Not Duplicate')
        plt.hist(tfidf_word_match_share[train_df['is_duplicate'] == 1].fillna(0), bins=20, normed=True, alpha=0.7,
                 label='Duplicate')
        plt.legend()
        plt.title('Label distribution over tfidf_word_match_share', fontsize=15)
        plt.xlabel('word_match_share', fontsize=15)
        plt.show()

    @staticmethod
    def demo():
        """
        使用样例
        :return: NONE
        """
        # 读取配置文件
        cf = ConfigParser.ConfigParser()
        cf.read("../conf/python.conf")

        # 加载train.csv文件
        train_data = pd.read_csv('%s/train.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 加载test.csv文件
        test_data = pd.read_csv('%s/test.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 特征文件路径
        feature_path = cf.get('DEFAULT', 'feature_question_pair_pt')
        # 提取特征
        TFIDFWordMatchShare.run(train_data, test_data, feature_path)


class MyWordMatchShare(object):
    """
    提取<Q1,Q2>特征：my_word_match_share
    """

    stops = set(stopwords.words("english"))

    @staticmethod
    def word_match_share(row):
        """
        针对单个<Q1,Q2>实例抽取特征
        :param row: DataFrame中的一行数据
        :return: 特征值
        """
        q1words = {}
        q2words = {}
        for word in str(row['question1']).lower().split():
            if word not in WordMatchShare.stops:
                q1words[word] = q1words.get(word, 0) + 1
        for word in str(row['question2']).lower().split():
            if word not in WordMatchShare.stops:
                q2words[word] = q2words.get(word, 0) + 1
        n_shared_word_in_q1 = sum([q1words[w] for w in q1words if w in q2words])
        n_shared_word_in_q2 = sum([q2words[w] for w in q2words if w in q1words])
        n_tol = sum(q1words.values()) + sum(q2words.values())
        if (1e-6 > n_tol):
            return [0.]
        else:
            return [1.0 * (n_shared_word_in_q1 + n_shared_word_in_q2) / n_tol]

    @staticmethod
    def run(train_df, test_df, feature_pt):
        """
        抽取train.csv test.csv特征
        :param train_df: train.csv数据
        :param test_df: test.csv数据
        :param feature_pt: 特征文件路径
        :return: None
        """
        train_features = train_df.apply(MyWordMatchShare.word_match_share, axis=1, raw=True)
        Feature.save_dataframe(train_features, feature_pt + '/my_word_match_share.train.smat')

        test_features = test_df.apply(MyWordMatchShare.word_match_share, axis=1, raw=True)
        Feature.save_dataframe(test_features, feature_pt + '/my_word_match_share.test.smat')

        my_word_match_share = train_features.apply(lambda x: x[0])
        plt.figure(figsize=(15, 5))
        plt.hist(my_word_match_share[train_df['is_duplicate'] == 0], bins=20, normed=True, label='Not Duplicate')
        plt.hist(my_word_match_share[train_df['is_duplicate'] == 1], bins=20, normed=True, alpha=0.7, label='Duplicate')
        plt.legend()
        plt.title('Label distribution over word_match_share', fontsize=15)
        plt.xlabel('word_match_share', fontsize=15)
        plt.show()

    @staticmethod
    def demo():
        """
        使用样例
        :return: NONE
        """
        # 读取配置文件
        cf = ConfigParser.ConfigParser()
        cf.read("../conf/python.conf")

        # 加载train.csv文件
        train_data = pd.read_csv('%s/train.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 加载test.csv文件
        test_data = pd.read_csv('%s/test.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 特征文件路径
        feature_path = cf.get('DEFAULT', 'feature_question_pair_pt')
        # 提取特征
        MyWordMatchShare.run(train_data, test_data, feature_path)


class MyTFIDFWordMatchShare(object):
    """
    基于TF-IDF的词共享特征
    """

    idf = {}

    @staticmethod
    def init_idf(data):
        """
        根据文档计算IDF，包括停用词
        :param data: DataFrame数据
        :return: IDF词典
        """
        idf = {}
        for index, row in data.iterrows():
            words = set(str(row['question']).lower().split())
            for word in words:
                idf[word] = idf.get(word, 0) + 1
        num_docs = len(data)
        for word in idf:
            idf[word] = math.log(num_docs / (idf[word] + 1.)) / math.log(2.)
        LogUtil.log("INFO", "IDF calculation done, len(idf)=%d" % len(idf))
        MyTFIDFWordMatchShare.idf = idf

    @staticmethod
    def tfidf_word_match_share(row):
        """
        针对一个<Q1,Q2>抽取特征
        :param row: 一个<Q1,Q2>实例
        :return: 特征值
        """
        q1words = {}
        q2words = {}
        for word in str(row['question1']).lower().split():
            q1words[word] = q1words.get(word, 0) + 1
        for word in str(row['question2']).lower().split():
            q2words[word] = q2words.get(word, 0) + 1
        sum_shared_word_in_q1 = sum([q1words[w] * MyTFIDFWordMatchShare.idf.get(w, 0) for w in q1words if w in q2words])
        sum_shared_word_in_q2 = sum([q2words[w] * MyTFIDFWordMatchShare.idf.get(w, 0) for w in q2words if w in q1words])
        sum_tol = sum(q1words[w] * MyTFIDFWordMatchShare.idf.get(w, 0) for w in q1words) + sum(q2words[w] * MyTFIDFWordMatchShare.idf.get(w, 0) for w in q2words)
        if 1e-6 > sum_tol:
            return [0.]
        else:
            return [1.0 * (sum_shared_word_in_q1 + sum_shared_word_in_q2) / sum_tol]

    @staticmethod
    def run(train_df, test_df, train_qid2question, feature_pt):
        """
        抽取train.csv和test.csv的<Q1,Q2>特征：my_tfidf_word_match_share
        :param train_df: train.csv
        :param test_df: test.csv
        :param train_qid2question: train.csv去重question集合
        :param feature_pt: 特征文件目录
        :return: None
        """
        # 获取weights信息
        MyTFIDFWordMatchShare.init_idf(train_qid2question)
        # 抽取特征
        train_features = train_df.apply(MyTFIDFWordMatchShare.tfidf_word_match_share, axis=1, raw=True)
        Feature.save_dataframe(train_features, feature_pt + '/my_tfidf_word_match_share.train.smat')
        test_features = test_df.apply(MyTFIDFWordMatchShare.tfidf_word_match_share, axis=1, raw=True)
        Feature.save_dataframe(test_features, feature_pt + '/my_tfidf_word_match_share.test.smat')
        # 绘图
        my_tfidf_word_match_share = train_features.apply(lambda x: x[0])
        plt.figure(figsize=(15, 5))
        plt.hist(my_tfidf_word_match_share[train_df['is_duplicate'] == 0].fillna(0), bins=20, normed=True,
                 label='Not Duplicate')
        plt.hist(my_tfidf_word_match_share[train_df['is_duplicate'] == 1].fillna(0), bins=20, normed=True, alpha=0.7,
                 label='Duplicate')
        plt.legend()
        plt.title('Label distribution over tfidf_word_match_share', fontsize=15)
        plt.xlabel('word_match_share', fontsize=15)
        plt.show()

    @staticmethod
    def demo():
        """
        使用样例
        :return: NONE
        """
        # 读取配置文件
        cf = ConfigParser.ConfigParser()
        cf.read("../conf/python.conf")

        # 加载train.csv文件
        train_data = pd.read_csv('%s/train.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 加载test.csv文件
        test_data = pd.read_csv('%s/test.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 特征文件路径
        feature_path = cf.get('DEFAULT', 'feature_question_pair_pt')
        # train.csv中去重question文件
        train_qid2q_fp = '%s/train_qid2question.csv' % cf.get('DEFAULT', 'devel_pt')
        train_qid2q = pd.read_csv(train_qid2q_fp).fillna(value="")
        # 提取特征
        MyTFIDFWordMatchShare.run(train_data, test_data, train_qid2q, feature_path)


class PowerfulWord(object):
    """
    寻找最有影响力的词
    """
    @staticmethod
    def cal_word_power(train_data, train_subset_indexs):
        """
        计算数据中词语的影响力，格式如下：
            词语 --> [0. 出现语句对数量，1. 出现语句对比例，2. 正确语句对比例，3. 单侧语句对比例，4. 单侧语句对正确比例，5. 双侧语句对比例，6. 双侧语句对正确比例]
        :param data: 训练数据
        :return: 影响力词典
        """
        words_power = {}
        train_subset_data = train_data.iloc[train_subset_indexs, :]
        for index, row in train_subset_data.iterrows():
            label = int(row['is_duplicate'])
            q1_words = str(row['question1']).lower().split()
            q2_words = str(row['question2']).lower().split()
            all_words = set(q1_words + q2_words)
            q1_words = set(q1_words)
            q2_words = set(q2_words)
            for word in all_words:
                if word not in words_power:
                    words_power[word] = [0. for i in range(7)]
                # 计算出现语句对数量
                words_power[word][0] += 1.
                words_power[word][1] += 1.

                if ((word in q1_words) and (word not in q2_words)) or ((word not in q1_words) and (word in q2_words)):
                    # 计算单侧语句数量
                    words_power[word][3] += 1.
                    if 0 == label:
                        # 计算正确语句对数量
                        words_power[word][2] += 1.
                        # 计算单侧语句正确比例
                        words_power[word][4] += 1.
                if (word in q1_words) and (word in q2_words):
                    # 计算双侧语句数量
                    words_power[word][5] += 1.
                    if 1 == label:
                        # 计算正确语句对数量
                        words_power[word][2] += 1.
                        # 计算双侧语句正确比例
                        words_power[word][6] += 1.
        for word in words_power:
            # 计算出现语句对比例
            words_power[word][1] /= len(train_subset_indexs)
            # 计算正确语句对比例
            words_power[word][2] /= words_power[word][0]
            # 计算单侧语句对正确比例
            if words_power[word][3] > 1e-6:
                words_power[word][4] /= words_power[word][3]
            # 计算单侧语句对比例
            words_power[word][3] /= words_power[word][0]
            # 计算双侧语句对正确比例
            if words_power[word][5] > 1e-6:
                words_power[word][6] /= words_power[word][5]
            # 计算双侧语句对比例
            words_power[word][5] /= words_power[word][0]
        sorted_words_power = sorted(words_power.iteritems(), key=lambda d: d[1][0], reverse=True)
        LogUtil.log("INFO", "power words calculation done, len(words_power)=%d" % len(sorted_words_power))
        return sorted_words_power

    @staticmethod
    def save_word_power(words_power, fp):
        """
        存储影响力词表
        :param words_power: 影响力词表
        :param fp: 存储路径
        :return: NONE
        """
        f = open(fp, 'w')
        for ele in words_power:
            f.write("%s" % ele[0])
            for num in ele[1]:
                f.write("\t%.5f" % num)
            f.write("\n")
        f.close()

    @staticmethod
    def run(train_data, train_subset_indexs, words_power_fp):
        # 计算词语影响力
        words_power = PowerfulWord.cal_word_power(train_data, train_subset_indexs)
        # 存储影响力词表
        PowerfulWord.save_word_power(words_power, words_power_fp)
        return

    @staticmethod
    def demo():
        """
        使用示例
        :return:
        """
        # 读取配置文件
        cf = ConfigParser.ConfigParser()
        cf.read("../conf/python.conf")

        # 加载train.csv文件
        train_data = pd.read_csv('%s/train.csv' % cf.get('DEFAULT', 'origin_pt')).fillna(value="")
        # 加载训练子集索引文件（NOTE: 不是训练集）
        train_subset_indexs = Feature.load_index(cf.get('MODEL', 'train_indexs_fp'))
        # 影响力词表路径
        words_power_fp = '%s/words_power.%s.txt' % (cf.get('DEFAULT', 'feature_stat_pt'), cf.get('MODEL', 'train_subset_name'))

        # 提取特征
        PowerfulWord.run(train_data, train_subset_indexs, words_power_fp)


if __name__ == "__main__":
    PowerfulWord.demo()