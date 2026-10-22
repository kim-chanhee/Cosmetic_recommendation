"""핵심 오류의 회귀 검증. 모델 다운로드나 전체 노트북 실행 없이 실행 가능.

실행: .venv/bin/python -m unittest discover -s tests -v
노트북에서 함수 정의만 AST로 읽어 실제 구현을 검증합니다.
"""
import ast
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code/common'))
from project_utils import add_review_ids, merge_sentiment, known_value, split_concerns, SCHEMA_VERSION
from skin_type_recommendations import recommend_by_skin_type


def notebook_functions():
    notebook = json.loads((ROOT/'code/04_추천시스템/recommend_products.ipynb').read_text())
    nodes = []
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            nodes.extend(n for n in ast.parse(''.join(cell['source'])).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)))
    namespace = dict(np=np, pd=pd, torch=torch, known_value=known_value, split_concerns=split_concerns,
                     SEED=42, SKIN_THRESHOLD=.1, CONTENT_WEIGHT=.5,
                     RESULT_COLUMNS=['item_id', 'final_score', 'content_score', 'cf_rating', 'content_norm', 'cf_norm', 'filter_status', 'strategy'])
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<notebook definitions>', 'exec'), namespace)
    return namespace


FN = notebook_functions()


def reviews_fixture():
    return pd.DataFrame({
        'review_id': ['r1', 'r2', 'r3', 'r4'],
        'user_id': ['u', 'v', 'w', 'u'], 'item_id': ['A', 'B', 'C', 'A'],
        'skin_type': ['건성', '지성', '건성', '건성'],
        'skin_tone': [None, '웜톤', None, None],
        'skin_concerns': ['모공 / 트러블', '모공', None, None],
        'date': pd.to_datetime(['2025-01-01', '2025-02-01', '2025-03-01', '2024-01-01']),
        'rating': [5., 4., 4., 3.], 'rating_aug': [5., 4., 4., 3.],
    })


class PipelineTests(unittest.TestCase):
    def test_skin_type_cohorts_have_separate_preferences(self):
        frame = pd.DataFrame(dict(user_id=['u', 'u', 'v', 'v'], item_id=['A', 'B', 'A', 'B'],
                                  skin_type=['건성', '건성', '지성', '지성'], rating=[5., 1., 1., 5.],
                                  review_id=['1', '2', '3', '4'], date=pd.to_datetime(['2025-01-01']*4)))
        class PreferenceModel:
            def predict(self, user, item):
                return 5. if (user, item) in {('u', 'A'), ('v', 'B')} else 1.
        state = dict(frame=frame, items=['A', 'B'], item_index={'A': 0, 'B': 1},
                     vectors=np.eye(2), model=PreferenceModel(), backend='observed_mf',
                     ratios={'skin_type': FN['get_ratio_pivot'](frame, 'skin_type')})
        result, summary = recommend_by_skin_type(state)
        self.assertEqual(result[result.skin_type == '건성'].iloc[0].item_id, 'A')
        self.assertEqual(result[result.skin_type == '지성'].iloc[0].item_id, 'B')
        self.assertTrue(result.groupby('skin_type').size().eq(2).all())
        self.assertTrue(result.final_score.between(0, 1).all())
        self.assertEqual(summary.loc[summary.skin_type == '민감성', 'recommended_count'].iloc[0], 0)
        # 타입 비율이 기준 미만이면 타 조건/전체 상품으로 완화하지 않습니다.
        empty, summary = recommend_by_skin_type(state, threshold=.6)
        self.assertTrue(empty.empty)
        self.assertTrue(summary.candidate_count.eq(0).all())

    def test_review_id_stable_after_shuffle(self):
        frame = pd.DataFrame({'product_name': ['A', 'B'], 'customer_name': ['u', 'v'], 'review': ['좋아요', '싫어요'], 'date': ['2025-01-01']*2})
        before = add_review_ids(frame)
        after = add_review_ids(frame.iloc[::-1])
        self.assertEqual(set(before.review_id), set(after.review_id))
        self.assertEqual(before.iloc[0].review_id, after.iloc[1].review_id)

    def test_merge_uses_id_not_row_order(self):
        reviews = pd.DataFrame({'review_id': ['a', 'b'], 'rating': [4, 2]})
        sentiment = pd.DataFrame({'review_id': ['b', 'a'], 'pred': [0, 1], 'positive_probability': [.2, .9],
                                  'sentiment_score': [-.6, .8], 'schema_version': [SCHEMA_VERSION]*2})
        merged = merge_sentiment(reviews, sentiment)
        self.assertEqual(merged.pred.tolist(), [1, 0])
        for bad in [sentiment.iloc[:1], pd.concat([sentiment, sentiment.iloc[:1]])]:
            with self.assertRaises(ValueError): merge_sentiment(reviews, bad)
        sentiment['pred'] = 1 - sentiment.pred
        with self.assertRaises(ValueError): merge_sentiment(reviews, sentiment)

    def test_missing_skin_never_expands_candidates(self):
        frame = reviews_fixture()
        ratios = {c: FN['get_ratio_pivot'](frame, c) for c in ['skin_type', 'skin_tone', 'skin_concerns']}
        state = {'frame': frame, 'items': ['A', 'B', 'C'], 'ratios': ratios}
        # u has dry skin + pore concern: A/C from type, B from pore. Remove concerns to isolate type.
        state['frame'] = frame.assign(skin_concerns=None)
        candidates, reason = FN['filter_items_by_skin_compatibility'](state, 'u')
        self.assertEqual(candidates, {'A', 'C'})
        self.assertEqual(reason, 'skin_filter_applied')
        self.assertNotIn('Unknown', ratios['skin_type'].columns)

    def test_skin_concerns_split_and_denominator(self):
        ratios = FN['get_ratio_pivot'](reviews_fixture(), 'skin_concerns')
        self.assertEqual(set(ratios.columns), {'모공', '트러블'})
        self.assertEqual(ratios.loc['A', '모공'], 1.)
        self.assertEqual(ratios.loc['B', '트러블'], 0.)

    def test_latest_valid_profile_is_date_ordered(self):
        frame = reviews_fixture()
        frame.loc[3, 'skin_type'] = '지성'  # last physical row is older
        self.assertEqual(FN['latest_user_profile'](frame, 'u')['skin_type'], '건성')

    def test_masked_pool_excludes_padding_and_special(self):
        hidden = torch.tensor([[[100., 100.], [2., 4.], [6., 8.], [999., 999.]]])
        vectors, counts = FN['masked_mean_pool'](hidden, torch.tensor([[1, 1, 1, 0]]), torch.tensor([[1, 0, 0, 1]]))
        np.testing.assert_allclose(vectors.numpy(), [[4., 6.]])
        self.assertEqual(counts.item(), 2)

    def test_mf_does_not_learn_missing_as_zero(self):
        frame = pd.DataFrame({'user_id': ['u1', 'u2', 'u3'], 'item_id': ['a', 'b', 'a'], 'rating_aug': [4.5]*3})
        model = FN['ObservedRatingMF'](n_epochs=40).fit(frame)
        self.assertGreater(model.predict('u1', 'b'), 4.)
        self.assertGreater(model.predict('new_user', 'b'), 4.)
        self.assertTrue(1 <= model.predict('new_user', 'new_item') <= 5)

    def test_duplicate_pairs_are_averaged(self):
        frame = pd.DataFrame({'user_id': ['u', 'u', 'v'], 'item_id': ['a', 'a', 'b'], 'rating_aug': [1., 5., 5.]})
        model, _ = FN['fit_collaborative'](frame, backend='observed_mf')
        self.assertEqual(model.global_mean, 4.)  # mean of (3,5), not of (1,5,5)

    def test_seen_items_removed_and_cold_start_stable(self):
        frame = reviews_fixture()
        vectors = np.array([[1., 0.], [0., 1.], [.8, .2], [1., 0.]])
        state = FN['build_recommender'](frame, vectors, backend='observed_mf')
        result = FN['recommend_hybrid_skin_filtered'](state, 'u')
        self.assertNotIn('A', result.item_id.tolist())
        new = FN['recommend_hybrid_skin_filtered'](state, 'new')
        self.assertEqual(new.item_id.tolist(), ['A', 'B', 'C'])
        self.assertTrue(new.strategy.eq('cold_start_popularity').all())
        again = FN['recommend_hybrid_skin_filtered'](state, 'new')
        pd.testing.assert_frame_equal(new, again)

    def test_holdout_removes_all_reviews_of_pair(self):
        frame = reviews_fixture()
        extra = frame.iloc[[0]].copy()
        extra['review_id'] = 'r5'; extra['item_id'] = 'B'; extra['date'] = pd.Timestamp('2026-01-01')
        duplicate = extra.copy(); duplicate['review_id'] = 'r6'
        frame = pd.concat([frame, extra, duplicate], ignore_index=True)
        mask, heldout = FN['make_holdout'](frame)
        self.assertIn(('u', 'B'), set(map(tuple, heldout.to_numpy())))
        self.assertFalse(((frame.loc[mask].user_id == 'u') & (frame.loc[mask].item_id == 'B')).any())
        self.assertEqual(int((~mask).sum()), 2)

    def test_normalization_handles_equal_and_invalid_values(self):
        self.assertEqual(FN['normalize_scores']({'a': 3., 'b': 3.}), {'a': .5, 'b': .5})
        with self.assertRaises(ValueError): FN['normalize_scores']({'a': np.nan})


if __name__ == '__main__':
    unittest.main()
