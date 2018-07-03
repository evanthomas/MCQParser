from xmltodict import parse
import sys
import os
import zipfile
from bs4 import BeautifulSoup

class MCQ:
  def __init__(self, presentation):
    flows = presentation['flow']['flow']
    
    self.answers = []
    for flow in flows:
      if flow['@class'] == 'QUESTION_BLOCK':
        self.question = self._extractQuestion(flow)
      if flow['@class'] == 'RESPONSE_BLOCK':
        self.answers = self._extractAnswers(flow)

  def _extractQuestion(self, xml):
    try:
      return self._clean(xml['flow']['material']['mat_extension']['mat_formattedtext'])
    except KeyError:
      raise Exception('Question not in expected format')

  def _extractAnswers(self, xml):
    answers = []
    try:
      answersXml = xml['response_lid']['render_choice']['flow_label']
      for answer in answersXml:
        at = self._clean(answer['response_label']['flow_mat']['material']['mat_extension']['mat_formattedtext'])
        answers.append(at)
    except KeyError:
      raise Exception('Answer not in expected format')

    return answers

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
    for a in self.answers:
      s = s + '   ' + str(n) + '. ' + a + '\n'
      n = n + 1
    return s

  def toHTML(self):
    s = '<p>' + self.question + '\n<ol>'
    for answer in self.answers:
      s = s + '<li>' + answer + '</li>\n'
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
        presentation = item['presentation']
        self.mcqs.append(MCQ(presentation))
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

  htmlFile = os.path.basename(inf) + '.html'
  with open(htmlFile, 'w') as f:
    f.write(html)

if __name__ == '__main__':
  main()