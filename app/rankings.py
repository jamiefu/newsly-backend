from app.models import Source, Article
from datetime import datetime, timedelta
import csv
from collections import defaultdict


metrics = ["rank","reputation","popularity", "breadth", "bias"]


def decay_fn(time, decay):
    days_since =  (datetime.now() - time).total_seconds() / (3600 * 24)
    ans =  1/(1+days_since)**decay
    return ans 

def sent_fn(a, x):
    ans = 1 / (1 + abs(a - 4 * x))**3
    return ans 

def generate_ranking(articles, P):
    SRC_MULTS = {"rank":P["SRC_RANK"],"reputation":P["SRC_REP"],"popularity":P["SRC_POP"], "breadth":P["SRC_BREADTH"], "bias":P["SRC_BIAS"]}
    FACTORS_MULTS = {"source":P["FACTOR_SOURCE"], "twitter":P["FACTOR_TWITTER"],"political":P["FACTOR_POLITICAL"]}

    articles = [a.serialize() for a in articles]
    sources = [a["news_metadata"]["source_id"] for a in articles if "source_id" in a["news_metadata"]]
    sources = Source.query.filter(Source.id.in_(set(sources))).all()
    src_metrics = get_src_metrics(sources)
    print(src_metrics)
    max_twitter = max([len(a["news_metadata"]["twitter_all"]) for a in articles if "twitter_all" in a["news_metadata"] ])
    scores = {a["id"]:0 for a in articles}
    running_scores = {a["id"]:{} for a in articles}

    for a in articles:
        metadata = a["news_metadata"]
        running_score = defaultdict(lambda: "")
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
            a["source_metrics"] = src_metrics[a["news_metadata"]["source_id"]]

        if len(metadata["twitter_all"]) > 3:
            # total = TWITTER_MULT
            score = (len(metadata["twitter_all"]) / max_twitter)
            ratio = len(metadata["twitter_local"])/len(metadata["twitter_all"])
            if ratio < P["TWITTER_RATIO"]:
                score += P["TWITTER_RATIO_BONUS"] * (1 - score)
            running_score["twitter"] = score

        if metadata["political_sents"] > 0:
            score = sent_fn(P["POLITICAL_SENTIMENT"], metadata["political_sentiment"]["comp"])
            score += P["POLITICAL_BONUS"] * (1 - score)
            running_score["political"] = score


        # print(Source.query.filter_by(id=a["news_metadata"]["source_id"]).first().name, running_score)
        
        final_score = 0
        total = 0
        for factor, score in running_score.items():
            final_score += FACTORS_MULTS[factor] * score
            # total += FACTORS_MULTS[factor]
        scores[a["id"]] = final_score * decay_fn(a["publish_date"], P["TIME_DECAY"]) # / total if total > 0 else 0
        print(decay_fn(a["publish_date"], P["TIME_DECAY"]),final_score, running_score, a["title"])
        running_scores[a["id"]] = running_score
    ranked_list = sorted([(scores[a["id"]], a) for a in articles], reverse=True, key=lambda x: x[0])
    print([(a[0],a[1]["title"]) for a in ranked_list])
    # with open("rankings_breakdown.csv","w") as f:
    #     writer = csv.writer(f)
    #     for score, a in ranked_list:
    #         sc = running_scores[a["id"]]
    #         writer.writerow([score, a["title"], a["url"], a["publish_date"], a["news_metadata"]["source_name"], sc["source"], sc["political"], sc["twitter"], decay_fn(a["publish_date"])])
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