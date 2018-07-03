# MCQParser
A simple tool for extracting multiple choice questions from a Backboard content package.

You will need to pip install xmltodict, zipfile, beautifulsoup4 and html5lib. Then just pass the zip file, no need to uncompress, 
and an html file is produced.  Obviously, I can produce something in another format if you like, e.g. markdown. For some
reason, some the text is wrapped in HTML and some isn’t. I’ve stripped any HTML wrapping.
