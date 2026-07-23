import re
from typing import List
from collections import Counter

def extract_high_frequency_words(text_list: List[str]) -> List[dict]:
    cleaned_texts = []
    for text in text_list:
        if not text:
            continue
        cleaned = re.sub(r'\[sticker:[^\]]+\]', '', text)
        cleaned_texts.append(cleaned)
        
    full_text = " ".join(cleaned_texts)
    
    try:
        import jieba
        words = []
        for word in jieba.cut(full_text):
            if len(word) >= 2 and re.match(r'^[\u4e00-\u9fa5]+$', word):
                if word not in ["今天", "我们", "你们", "他们", "自己", "一个", "时候", "可以", "觉得", "非常", "特别", "感觉"]:
                    words.append(word)
    except ImportError:
        candidates = re.findall(r'[\u4e00-\u9fa5]{2,5}', full_text)
        words = []
        stop_words = ["今天", "我们", "你们", "他们", "自己", "一个", "时候", "可以", "觉得", "非常", "特别", "感觉", "也是", "还是", "因为", "所以", "但是", "没有", "这个", "那个", "很多", "东西"]
        for w in candidates:
            if w not in stop_words:
                words.append(w)
                
    counter = Counter(words)
    top_words = counter.most_common(12)
    return [{"text": k, "value": v} for k, v in top_words]
