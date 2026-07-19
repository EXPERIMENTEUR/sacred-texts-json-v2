import spacy

nlp = spacy.load("en_core_web_sm")

ruler = nlp.add_pipe("entity_ruler", before="ner")

patterns = [
    {"label": "DEITY", "pattern": "God"},
    {"label": "DEITY", "pattern": "Yahweh"},
    {"label": "DEITY", "pattern": "Agni"},
    {"label": "DEITY", "pattern": "Indra"},
    {"label": "DEITY", "pattern": "Thoth"},
    {"label": "SACRED_PLACE", "pattern": [{"LOWER": "mount"}, {"LOWER": "sinai"}]},
    {"label": "SACRED_OBJECT", "pattern": [{"LOWER": "book"}, {"LOWER": "of"}, {"LOWER": "thoth"}]},
]

ruler.add_patterns(patterns)

texte = "In the beginning God created the heaven and the earth."
doc = nlp(texte)

print("--- Entites nommees (avec EntityRuler) ---")
for ent in doc.ents:
    print(ent.text, "->", ent.label_)