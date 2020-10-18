import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize, word_tokenize
from app.political_words import POLITICAL_WORDS


DEFAULT_PARAMS = {
    
}

def political_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    sentences = sent_tokenize(text)

    result = []
    for sent in sentences:
        words = set(word_tokenize(sent))
        if POLITICAL_WORDS.intersection(words):
            result.append(sid.polarity_scores(sent))
            # print(f"{sid.polarity_scores(sent)}\n{sent}")

    n = len(result)
    if n:
        neg = sum([r['neg'] for r in result])/n
        neu = sum([r['neu'] for r in result])/n
        pos = sum([r['pos'] for r in result])/n
        compound = sum([r['compound'] for r in result])/n
        return n, len(sentences), {'neg':neg, 'neu':neu, 'pos':pos, 'comp':compound}
    else:
        return 0, len(sentences), {'neg':0, 'neu':0,'pos':0, 'comp':0}






if __name__ == '__main__':
    # s = "Riot police have used water cannon to disperse thousands of protesters, including school students, gathered in Bangkok as Thai authorities intensified a crackdown on demonstrations led by young people calling for reform of the monarchy.\n\nBlasts of blue-coloured water were fired at demonstrators who had assembled for a second day in defiance of “severe” emergency measures introduced this week in response to an unprecedented pro-democracy movement that has swept across Thailand over recent months.\n\nThe protesters have shocked many by calling for reforms to the country’s hugely wealthy and powerful monarchy – an institution protected by a harsh defamation law, and that has long been considered untouchable. The movement is led by university and school students, but has attracted support from older generations.\n\nAs police moved forwards, teenagers wearing school uniforms ran to safety, while some protesters attempted to shield themselves with umbrellas. One woman could be heard screaming at police: “How can you do this?” Protesters said the water contained chemical irritants.\n\nPolice had blocked roads in an attempt to stop the protests, but student leaders switched their assembly point at the last minute. Earlier in the afternoon, services from key train stations were halted and police raided the offices of the Progressive Movement, a group formed by banned politicians from the disbanded opposition party Future Forward."
    s = """Such deadly accidents are common in Thailand, which regularly tops lists of countries with the world’s most lethal roads, with speeding, drunk driving and weak law enforcement all contributing factors.

According to a 2018 report by the World Health Organization, Thailand has the second-highest traffic fatality rate in the world.

Though a majority of the victims are motorcyclists, bus crashes involving groups of tourists and migrant labourers often grab headlines.

In March 2018, at least 18 people were killed and dozens wounded when a bus carrying people returning from holiday in northeastern Thailand swerved off the road and smashed into a tree."""
    print(political_sentiment(s))