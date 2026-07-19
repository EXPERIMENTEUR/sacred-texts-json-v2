import spacy

nlp = spacy.load("en_core_web_sm")
texte = "Napoleon Bonaparte was born in Corsica in 1769 and became Emperor of France."
doc = nlp(texte)

print("--- Entites nommees ---")
for ent in doc.ents:
    print(ent.text, "->", ent.label_)

print("--- Mots et grammaire ---")
for token in doc:
    print(token.text, token.pos_, token.lemma_)