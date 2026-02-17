from experta import *

class MedicalExpert(KnowledgeEngine):

    def __init__(self):
        super().__init__()
        self.result = None


    @Rule(Fact(fever=True), Fact(headache=True), Fact(vomiting=True))
    def malaria(self):
        self.result = "Possible malaria or infection"


    @Rule(Fact(chest_pain=True))
    def heart(self):
        self.result = "Possible heart emergency"


    @Rule(Fact(bleeding=True))
    def bleed(self):
        self.result = "Possible serious bleeding"
