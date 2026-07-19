import spacy

nlp = spacy.load("en_core_web_sm")

ruler = nlp.add_pipe("entity_ruler", before="ner")
ruler.from_disk("patterns_religieux.jsonl")

texte = "Moses went up Mount Sinai and saw God in a pillar of fire, near the Ark of the Covenant."
doc = nlp(texte)

print("--- Entites nommees ---")
for ent in doc.ents:
    print(ent.text, "->", ent.label_)