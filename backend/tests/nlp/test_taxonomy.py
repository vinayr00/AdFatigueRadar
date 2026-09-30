"""
Tests for 8-Class Ad-Fatigue Taxonomy Classifier
"""

import pytest
from backend.nlp.taxonomy import TaxonomyClassifier
from backend.nlp import (
    TAXONOMY_CATEGORIES,
    CRITICAL_COMPLAINT_CATEGORIES,
    CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD,
)


@pytest.fixture
def taxonomy_classifier():
    return TaxonomyClassifier()


def test_taxonomy_classes_complete():
    assert len(TAXONOMY_CATEGORIES) == 8
    expected = {
        "product_complaint",
        "service_complaint",
        "fatigue",
        "mockery",
        "spam",
        "banter_meme",
        "neutral",
        "positive",
    }
    assert set(TAXONOMY_CATEGORIES) == expected


def test_again_disambiguation_rule(taxonomy_classifier):
    # Rule: 'again' means fatigue ONLY when repeated ad exposure is indicated.
    # 1. Ad fatigue cases
    fatigue_text_1 = "Bro this ad again 😂"
    cat1, conf1, crit1, _ = taxonomy_classifier.classify(fatigue_text_1)
    assert cat1 == "fatigue"
    assert crit1 is False

    fatigue_text_2 = "Stop showing me this same ad again and again"
    cat2, conf2, crit2, _ = taxonomy_classifier.classify(fatigue_text_2)
    assert cat2 == "fatigue"

    # 2. Positive repeat purchase cases
    pos_text_1 = "Bought again, love it!"
    cat_pos1, conf_pos1, _, _ = taxonomy_classifier.classify(pos_text_1)
    assert cat_pos1 == "positive"

    pos_text_2 = "Ordered again, thank you for the fast shipping!"
    cat_pos2, conf_pos2, _, _ = taxonomy_classifier.classify(pos_text_2)
    assert cat_pos2 == "positive"


def test_mockery_vs_banter_separation(taxonomy_classifier):
    # Mockery directed at ad/commercial
    mockery_text = "The acting in this commercial is killing me 💀 who approved this"
    cat_m, conf_m, crit_m, _ = taxonomy_classifier.classify(mockery_text)
    assert cat_m == "mockery"

    # Harmless meme banter
    banter_text = "Bro got that unspoken rizz let him cook 🔥"
    cat_b, conf_b, crit_b, _ = taxonomy_classifier.classify(banter_text)
    assert cat_b == "banter_meme"
    assert crit_b is False


def test_product_and_service_complaints(taxonomy_classifier):
    prod_text = "The product broke on day 2, cheap plastic defect"
    cat_p, conf_p, crit_p, _ = taxonomy_classifier.classify(prod_text)
    assert cat_p == "product_complaint"

    serv_text = "Ordered 3 weeks ago and support refuses to issue a refund or reply"
    cat_s, conf_s, crit_s, _ = taxonomy_classifier.classify(serv_text)
    assert cat_s == "service_complaint"


def test_critical_complaint_confidence_gate(taxonomy_classifier):
    # High confidence defect -> critical
    high_crit_text = "Dangerous defective product that short circuited and broke immediately"
    cat, conf, is_critical, _ = taxonomy_classifier.classify(high_crit_text)
    assert cat in CRITICAL_COMPLAINT_CATEGORIES
    if conf >= CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD:
        assert is_critical is True
    else:
        assert is_critical is False


def test_keyword_alone_cannot_force_critical_complaint(taxonomy_classifier):
    # A positive text with word 'broken' in a non-complaint context or banter
    text = "Bro this price is broken, such an amazing deal bought again!"
    cat, conf, is_critical, _ = taxonomy_classifier.classify(text)
    assert is_critical is False
    assert cat != "product_complaint"
