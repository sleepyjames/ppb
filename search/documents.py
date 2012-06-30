
from indexes import DocumentModel, TextField, IntegerField

class TestDocument(DocumentModel):
    text = TextField()
    number = IntegerField(default=0)
