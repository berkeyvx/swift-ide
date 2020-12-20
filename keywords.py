class SwiftKeywords(object):
    def __init__(self):
        self.keyword_list = {"break", "case", "continue", "default",
                             "do", "else", "fallthrough", "for",
                             "if", "in", "return", "switch", "where", "while"}
        
    def is_keyword(self, word):
        return (word in self.keyword_list)
        
    