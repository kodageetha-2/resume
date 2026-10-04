import pandas as pd
def prompt_comparison(zero, few):
    return pd.DataFrame([{"Prompt type":"Zero-shot","Output quality":"Baseline","Relevance":"Review manually","Completeness":"Review manually","Hallucination/error observations":"Check against resume facts","Output":zero}, {"Prompt type":"Few-shot","Output quality":"Structured","Relevance":"Review manually","Completeness":"Review manually","Hallucination/error observations":"Check against resume facts","Output":few}])
