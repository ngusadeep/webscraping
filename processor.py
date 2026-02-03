"""NLP processing for knowledge base enhancement (keywords, summaries, search)."""

import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple, Optional
import json
from datetime import datetime
import os
from dataclasses import dataclass, asdict
from scraper import KnowledgeBase, ScrapedContent


@dataclass
class ProcessedContent:
    original_content: ScrapedContent
    sentences: List[str]
    keywords: List[str]
    word_frequencies: Dict[str, int]
    summary: str
    key_phrases: List[str]
    readability_score: float


@dataclass
class EnhancedKnowledgeBase:
    """Enhanced knowledge base with processing"""

    original_kb: KnowledgeBase
    processed_content: List[ProcessedContent]
    global_keywords: List[str]
    topic_clusters: Dict[str, List[str]]
    search_index: Dict[str, List[int]]
    statistics: Dict[str, any]
    processed_at: str


class TextProcessor:
    def __init__(self):
        try:
            nltk.data.find("tokenizers/punkt")
            nltk.data.find("corpora/stopwords")
            nltk.data.find("corpora/wordnet")
        except LookupError:
            print("Downloading NLTK resources...")
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)
            nltk.download("wordnet", quiet=True)

        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))
        self.stop_words.update(
            [
                "http",
                "https",
                "www",
                "com",
                "org",
                "net",
                "html",
                "php",
                "asp",
                "click",
                "here",
                "read",
                "more",
                "contact",
                "home",
                "about",
                "services",
            ]
        )

    def clean_text_for_nlp(self, text: str) -> str:
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"[^\w\s\.\-\n]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def extract_sentences(self, text: str) -> List[str]:
        try:
            sentences = sent_tokenize(text)
            meaningful_sentences = [
                sent.strip()
                for sent in sentences
                if len(sent.strip()) > 20 and not sent.strip().startswith("http")
            ]
            return meaningful_sentences
        except Exception:
            sentences = [s.strip() + "." for s in text.split(".") if s.strip()]
            return sentences[:50]

    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        try:
            words = word_tokenize(text.lower())
            filtered_words = [
                word
                for word in words
                if word.isalpha() and word not in self.stop_words and len(word) > 2
            ]
            lemmatized_words = [
                self.lemmatizer.lemmatize(word) for word in filtered_words
            ]
            word_freq = Counter(lemmatized_words)
            keywords = [word for word, _ in word_freq.most_common(max_keywords)]

            return keywords

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []

    def calculate_readability(self, text: str) -> float:
        """Calculate a simple readability score"""
        sentences = self.extract_sentences(text)
        words = [word for sent in sentences for word in word_tokenize(sent)]

        if not sentences:
            return 0.0

        avg_words_per_sentence = len(words) / len(sentences)
        avg_syllables_per_word = sum(
            self.count_syllables(word) for word in words
        ) / len(words)
        readability = (
            206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables_per_word
        )
        return max(0, min(100, readability))

    def count_syllables(self, word: str) -> int:
        word = word.lower()
        count = 0
        vowels = "aeiouy"

        if word[0] in vowels:
            count += 1

        for i in range(1, len(word)):
            if word[i] in vowels and word[i - 1] not in vowels:
                count += 1

        if word.endswith("e"):
            count -= 1

        return max(1, count)

    def generate_summary(self, text: str, max_sentences: int = 5) -> str:
        sentences = self.extract_sentences(text)
        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        scored_sentences = []
        for i, sent in enumerate(sentences):
            position_score = 1.0 / (i + 1)
            length_score = min(len(sent.split()) / 20, 1.0)
            keywords = self.extract_keywords(sent, max_keywords=5)
            keyword_score = len(keywords) / 10
            total_score = position_score + length_score + keyword_score
            scored_sentences.append((total_score, sent))

        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [sent for _, sent in scored_sentences[:max_sentences]]
        sentence_dict = {sent: i for i, sent in enumerate(sentences)}
        top_sentences.sort(key=lambda x: sentence_dict.get(x, 999))

        return " ".join(top_sentences)

    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        sentences = self.extract_sentences(text)
        phrases = []

        for sentence in sentences:
            words = word_tokenize(sentence)
            tagged = nltk.pos_tag(words)

            current_phrase = []
            for word, tag in tagged:
                if tag.startswith("NN") or tag.startswith("JJ"):
                    current_phrase.append(word)
                else:
                    if len(current_phrase) >= 2:
                        phrases.append(" ".join(current_phrase))
                    current_phrase = []

            if len(current_phrase) >= 2:
                phrases.append(" ".join(current_phrase))

        phrase_freq = Counter(phrases)
        top_phrases = [phrase for phrase, _ in phrase_freq.most_common(max_phrases)]

        return top_phrases

    def process_content(self, content: ScrapedContent) -> ProcessedContent:
        text = content.text_content

        if not text:
            return ProcessedContent(
                original_content=content,
                sentences=[],
                keywords=[],
                word_frequencies={},
                summary="",
                key_phrases=[],
                readability_score=0.0,
            )

        sentences = self.extract_sentences(text)
        keywords = self.extract_keywords(text)
        words = [
            word
            for sent in sentences
            for word in word_tokenize(sent.lower())
            if word.isalpha() and word not in self.stop_words and len(word) > 2
        ]
        word_frequencies = dict(Counter(words).most_common(50))
        summary = self.generate_summary(text)
        key_phrases = self.extract_key_phrases(text)
        readability_score = self.calculate_readability(text)

        return ProcessedContent(
            original_content=content,
            sentences=sentences,
            keywords=keywords,
            word_frequencies=word_frequencies,
            summary=summary,
            key_phrases=key_phrases,
            readability_score=readability_score,
        )

    def build_search_index(
        self, processed_content: List[ProcessedContent]
    ) -> Dict[str, List[int]]:
        search_index = defaultdict(list)

        for i, content in enumerate(processed_content):
            for keyword in content.keywords:
                search_index[keyword.lower()].append(i)
            for phrase in content.key_phrases:
                phrase_words = phrase.lower().split()
                if len(phrase_words) >= 2:
                    search_index[" ".join(phrase_words)].append(i)

        return dict(search_index)

    def cluster_topics(
        self, processed_content: List[ProcessedContent]
    ) -> Dict[str, List[str]]:
        all_keywords = set()
        for content in processed_content:
            all_keywords.update(content.keywords)
        clusters = defaultdict(list)
        for keyword in sorted(all_keywords):
            first_letter = keyword[0].upper()
            clusters[first_letter].append(keyword)

        return dict(clusters)

    def process_knowledge_base(self, kb: KnowledgeBase) -> EnhancedKnowledgeBase:
        print("Processing knowledge base with NLP...")
        processed_content = []
        for content in kb.scraped_pages:
            processed = self.process_content(content)
            processed_content.append(processed)

        search_index = self.build_search_index(processed_content)
        topic_clusters = self.cluster_topics(processed_content)
        all_keywords = []
        for content in processed_content:
            all_keywords.extend(content.keywords)

        keyword_freq = Counter(all_keywords)
        global_keywords = [kw for kw, _ in keyword_freq.most_common(100)]
        total_sentences = sum(len(content.sentences) for content in processed_content)
        avg_readability = (
            sum(content.readability_score for content in processed_content)
            / len(processed_content)
            if processed_content
            else 0
        )

        statistics = {
            "total_processed_pages": len(processed_content),
            "total_sentences": total_sentences,
            "avg_readability_score": avg_readability,
            "unique_keywords": len(set(all_keywords)),
            "total_keywords": len(all_keywords),
        }

        return EnhancedKnowledgeBase(
            original_kb=kb,
            processed_content=processed_content,
            global_keywords=global_keywords,
            topic_clusters=topic_clusters,
            search_index=search_index,
            statistics=statistics,
            processed_at=datetime.now().isoformat(),
        )

    def save_enhanced_kb(
        self, enhanced_kb: EnhancedKnowledgeBase, output_dir: str = "enhanced_kb"
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)

        safe_domain = re.sub(r"[^\w\-_.]", "_", enhanced_kb.original_kb.domain)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_domain}_enhanced_kb_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        kb_dict = {
            "original_kb": asdict(enhanced_kb.original_kb),
            "processed_content": [
                asdict(content) for content in enhanced_kb.processed_content
            ],
            "global_keywords": enhanced_kb.global_keywords,
            "topic_clusters": enhanced_kb.topic_clusters,
            "search_index": enhanced_kb.search_index,
            "statistics": enhanced_kb.statistics,
            "processed_at": enhanced_kb.processed_at,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(kb_dict, f, indent=2, ensure_ascii=False)

        print(f"Enhanced knowledge base saved to: {filepath}")
        return filepath

    def search_kb(
        self, enhanced_kb: EnhancedKnowledgeBase, query: str
    ) -> List[Tuple[int, ProcessedContent, float]]:
        query_words = query.lower().split()
        relevant_content = []

        for i, content in enumerate(enhanced_kb.processed_content):
            score = 0
            for word in query_words:
                if word in content.keywords:
                    score += 2
                if word in content.original_content.title.lower():
                    score += 3
            for phrase in content.key_phrases:
                if any(word in phrase.lower() for word in query_words):
                    score += 1.5
            if any(
                word in content.original_content.text_content.lower()
                for word in query_words
            ):
                score += 1

            if score > 0:
                relevant_content.append((i, content, score))

        relevant_content.sort(key=lambda x: x[2], reverse=True)
        return relevant_content[:10]
