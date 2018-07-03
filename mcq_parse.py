from xmltodict import parse
import sys
import os
import zipfile
from bs4 import BeautifulSoup

class Choice:
  def __init__(self, choice_text, id):
    self.choice_text = choice_text
    self.id = id

  def is_correct(self, id):
    return id == self.id

class MCQ:
  def __init__(self, item):

    flows = item['presentation']['flow']['flow']

    self.answers = []
    for flow in flows:
      if flow['@class'] == 'QUESTION_BLOCK':
        self.question = self._extractQuestion(flow)
      if flow['@class'] == 'RESPONSE_BLOCK':
        self.choices = self._extractChoices(flow)

    self.correct_choice_id = None
    response_conditions = item['resprocessing']['respcondition']
    for response_condition in response_conditions:
      try:
        if response_condition['@title'] == 'correct':
          self.correct_choice_id = response_condition['conditionvar']['varequal']['#text']
      except KeyError:
        pass

  def _extractQuestion(self, xml):
    try:
      return self._clean(xml['flow']['material']['mat_extension']['mat_formattedtext'])
    except KeyError:
      raise Exception('Question not in expected format')

  def _extractChoices(self, xml):
    choices = []
    try:
      choicesXml = xml['response_lid']['render_choice']['flow_label']
      for c in choicesXml:
        at = self._clean(c['response_label']['flow_mat']['material']['mat_extension']['mat_formattedtext'])
        id = c['response_label']['@ident']
        choices.append(Choice(at, id))
    except KeyError:
      raise Exception('Choice not in expected format')

    return choices

  def _extractAnswers(self, xml):
    pass

  def _clean(self, xml):
    text = xml['#text']
    formatting = xml['@type']
    if formatting == 'HTML':
      soup = BeautifulSoup(text, "html5lib")
      text = soup.get_text()
    return text

  def __str__(self):
    s = self.question + '\n'
    n = 1
    for a in self.choiced:
      if a.is_correct(self.correct_choice_id):
        ast = '* '
      else:
        ast = ''
      s = s + '   ' + str(n) + '. ' + ast + a.choice_text + '\n'
      n = n + 1
    return s

  def toHTML(self):
    s = '<p>' + self.question + '\n<ol>'
    for choice in self.choices:
      if choice.is_correct(self.correct_choice_id):
        tt = '<b>' + choice.choice_text + '</b>'
      else:
        tt = choice.choice_text
      s = s + '<li>' + tt + '</li>\n'
    s = s + '</ol>\n</p><br>\n'
    return s


class Resource:
  def __init__(self, xml, zf):
    self.file  = xml['@bb:file']
    self.title = xml['@bb:title']
    self.id    = xml['@identifier']
    self.type  = xml['@type']
    self.base  = xml['@xml:base']

    raw = zf.read(self.file)
    self.xml = parse(raw)

    try:
      items = self.xml['questestinterop']['assessment']['section']['item']
    except KeyError:
      items = []

    self.mcqs = []
    for item in items:
      try:
        self.mcqs.append(MCQ(item))
      except KeyError:
        pass

  def __str__(self):
    s = ''
    for m in self.mcqs:
      s = s + str(m) + '\n'
    return s

  def toHTML(self):
    s = ''
    for m in self.mcqs:
      s = s + m.toHTML() + '\n'
    return s


def process_manifest(zf):
  raw = zf.read('imsmanifest.xml')
  xml = parse(raw)

  xml_resources = xml['manifest']['resources']
  resources = []
  for xml_resource in xml_resources['resource']:
    resource = Resource(xml_resource, zf)
    resources.append(resource)

  return resources


def main():
  inf = sys.argv[1]
  zf = zipfile.ZipFile(inf, 'r')
  resources = process_manifest(zf)

  html = '<!DOCTYPE html>\n<html>\n<body>\n'
  for resource in resources:
    html = html + resource.toHTML()
  html = html + '</body>\n</html>'

  htmlFile = os.path.join(os.path.dirname(inf), os.path.basename(inf) + '.html')
  with open(htmlFile, 'w') as f:
    f.write(html)

if __name__ == '__main__':
  main()
