import re
import wikipedia
import unidecode
import spacy
import torch
from timeit import default_timer as timer
from transformers import AutoTokenizer, AutoModelForQuestionAnswering

wikipedia.set_lang('es')

def first_page(url):
    s = wikipedia.search(url)
    if len(s) > 0:
        return wikipedia.page(s[0])
    return None

def clean_page(url):
    page = first_page(url)
    if not page:
        return None
    
    content = page.content

    content = re.sub(r'\[\d+\]', '', content)
    content = re.sub(r'\u200b', '', content)

    content = unidecode.unidecode(content)

    content = content.split('\n')

    clean_content = []
    for c in content:
        c = c.replace('<', '').replace('>', '')
        if len(c) == 0:
            continue
        if c.startswith('='):
            continue
        clean_content.append(c)

    return clean_content


class BetoQA:
    def __init__(self):
        self.max_score = 0
        self.best_answer = ""
        self.incomplete_search = False
        self.page_content = []
        self.nlp = spacy.load('es_core_news_sm')
        self.tokenizer = AutoTokenizer.from_pretrained("mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es")
        self.model = AutoModelForQuestionAnswering.from_pretrained("mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es")


    def process_message(self, message):
        if self.incomplete_search:
            if message.lower() not in [
                "muestrame mas",
                "sigue buscando",
                "busca mas",
                "si",
                "no es lo que esperaba",
                "no creo que sea correcto"]:
                self.incomplete_search = False
                self.best_answer = ''
                self.max_score = 0
            else:
                response = self.process_qa(message)
                if self.incomplete_search:
                    response += "\n\n---------------------\nSi esta respuesta es incorrecta o no es lo que buscabas, puedo seguir buscando."
                return response
                
        if message.endswith('?'):
            response = self.process_qa(message)
            if self.incomplete_search:
                response += "\n\n---------------------\nSi esta respuesta es incorrecta o no es lo que buscabas, puedo seguir buscando."
        else:
            response = "Entendido"

        return response

    def process_qa(self, question):
        doc = self.nlp(question)

        if len(doc.ents) > 0:
            query = doc.ents[0].text
        else:
            query = question
        
        page = clean_page(query)
        if not page:
            self.incomplete_search = False
            self.max_score = 0
            self.best_answer = ""
            return "Lo siento, no encontre respuesta a tu pregutna. Intenta reformular tu pregunta"
        else:
            start = timer()
            for i, paragraph in enumerate(page):
                try:
                    score, answer = self.search_qa(question, paragraph)
                except:
                    pass

                if answer:
                    if  score > self.max_score:
                        self.max_score = score
                        self.best_answer = answer
                
                if(timer() - start > 15):
                    if i < len(page)-1:
                        self.incomplete_search = True
                    else:
                        self.incomplete_search = False
                    return self.best_answer
            return "Lo siento, no encontre respuesta a tu pregutna. Intenta reformular tu pregunta"

    def search_qa(self, question, context):
        tokens_c = self.tokenizer.tokenize(context)
        tokens_q = self.tokenizer.tokenize(question)

        tokens = ['[CLS]'] + tokens_q + ['[SEP]']
        seg_mask = [0] * len(tokens)
        tokens += tokens_c + ['[SEP]']
        seg_mask += [1] * len(tokens_c + ['[SEP]'])

        #print(tokens)

        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)

        output = self.model(torch.tensor([input_ids]), token_type_ids=torch.tensor([seg_mask]))

        answer_start = torch.argmax(output.start_logits)
        answer_end = torch.argmax(output.end_logits)

        score = torch.max(output.start_logits) + torch.max(output.end_logits)

        if answer_end >= answer_start:
            return score, ' '.join(tokens[answer_start:answer_end+1]).replace(' ##', '').replace('[CLS]', '').replace('[SEP]', '')
        return score, None
