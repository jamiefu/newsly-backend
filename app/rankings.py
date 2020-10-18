from app.models import Source, Article
from datetime import datetime, timedelta
SRC_MULTS = {"rank":1.5,"reputation":1,"popularity":1, "breadth":0.5, "bias":-1}
FACTORS_MULTS = {"source":0.7, "twitter":0.1,"political":0.2}
# TWITTER_MULT = 1
TWITTER_RATIO_BONUS = 0.5
TWITTER_RATIO = 0.4

POLITICAL_BONUS = 0.5
POLITICAL_SENTIMENT = -0.2

TIME_DECAY = 1.5

metrics = ["rank","reputation","popularity", "breadth", "bias"]


def decay_fn(time):
    days_since =  (datetime(2020, 10, 18, 6, 11, 29, 219333)- time).seconds / (3600 * 24)
    ans =  1/(1+days_since)**TIME_DECAY
    return ans 

def sent_fn(a, x):
    ans = 1 / (1 + abs(a - 4 * x))**3
    return ans 

def generate_ranking(articles):
    articles = [a.serialize() for a in articles]
    sources = [a["news_metadata"]["source_id"] for a in articles if "source_id" in a["news_metadata"]]
    sources = Source.query.filter(Source.id.in_(set(sources))).all()
    src_metrics = get_src_metrics(sources)
    print(src_metrics)
    max_twitter = max([len(a["news_metadata"]["twitter_all"]) for a in articles if "twitter_all" in a["news_metadata"] ])
    scores = {a["id"]:0 for a in articles}
    for a in articles:
        metadata = a["news_metadata"]
        running_score = {}
        if "source_id" in a["news_metadata"]:
            total = 0
            src_score = 0
            for metric, perc in src_metrics[a["news_metadata"]["source_id"]].items():
                if perc is not None:
                    mult = SRC_MULTS[metric]
                    if mult < 0:
                        perc = 1 - perc
                        mult = abs(mult)
                    total += mult
                    src_score += mult * perc
            running_score["source"] = src_score / total if total > 0 else 0

        if len(metadata["twitter_all"]) > 3:
            # total = TWITTER_MULT
            score = (len(metadata["twitter_all"]) / max_twitter)
            ratio = len(metadata["twitter_local"])/len(metadata["twitter_all"])
            if ratio < TWITTER_RATIO:
                score += TWITTER_RATIO_BONUS * (1 - score)
            running_score["twitter"] = score

        if metadata["political_sents"] > 0:
            score = sent_fn(POLITICAL_SENTIMENT, metadata["political_sentiment"]["comp"])
            score += POLITICAL_BONUS * (1 - score)
            running_score["political"] = score


        # print(Source.query.filter_by(id=a["news_metadata"]["source_id"]).first().name, running_score)
        
        final_score = 0
        total = 0
        for factor, score in running_score.items():
            final_score += FACTORS_MULTS[factor] * score
            # total += FACTORS_MULTS[factor]
        scores[a["id"]] = final_score * decay_fn(a["publish_date"]) # / total if total > 0 else 0
        print(decay_fn(a["publish_date"]), final_score, running_score, a["title"])
    ranked_list = sorted([(scores[a["id"]], a) for a in articles], reverse=True, key=lambda x: x[0])
    print([(a[0],a[1]["title"]) for a in ranked_list])
    return ranked_list


def get_src_metrics(sources):
    result = {s.id:{m:None for m in metrics} for s in sources}
    for m in metrics:
        data = [int(getattr(s, m)) for s in sources if getattr(s, m) is not None]
        if len(data) < 2:
            continue
        max_m = max(data)
        min_m = min(data)
        for s in sources:
            attr = getattr(s,m)
            if attr is not None:
                result[s.id][m] = 1 - (int(attr) - min_m) / (max_m - min_m)
    return result