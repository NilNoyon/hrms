from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import PyPDF2
import pandas as pd
from PyPDF2.generic import TextStringObject, ContentStream, IndirectObject, NameObject

#Multiple Documentation
#https://programtalk.com/python-examples-amp/xhtml2pdf.pisa.pisaDocument/ 
#PDF convert and generate link
#https://gearheart.io/blog/how-generate-pdf-files-python-xhtml2pdf-weasyprint-or-unoconv/
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    #pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    #pdf = pisa.pisaDocument(BytesIO(html.encode("ascii",'xmlcharrefreplace')), result)
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def b_(s):
    if type(s) == bytes:
        return s
    else:
        try:
            r = s.encode("latin-1")
            return r
        except Exception:
            r = s.encode("utf-8")
            return r

class PageObject2(PyPDF2.PageObject):
    def extractText(self, Tj_sep="", TJ_sep=""):
        """
        Locate all text drawing commands, in the order they are provided in the
        content stream, and extract the text.  This works well for some PDF
        files, but poorly for others, depending on the generator used.  This will
        be refined in the future.  Do not rely on the order of text coming out of
        this function, as it will change if this function is made more
        sophisticated.

        :return: a unicode string object.
        """
        text = PyPDF2.u_("")
        content = self["/Contents"].getObject()
        if not isinstance(content, ContentStream):
            content = ContentStream(content, self.pdf)
        # Note: we check all strings are TextStringObjects.  ByteStringObjects
        # are strings where the byte->string encoding was unknown, so adding
        # them to the text here would be gibberish.
        for operands, operator in content.operations:
            if operator == b_("Tj"):
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += Tj_sep
                    text += _text
            elif operator == b_("T*"):
                text += "\n"
            elif operator == b_("'"):
                text += "\n"
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += operands[0]
            elif operator == b_('"'):
                _text = operands[2]
                if isinstance(_text, TextStringObject):
                    text += "\n"
                    text += _text
            elif operator == b_("TJ"):
                for i in operands[0]:
                    if isinstance(i, TextStringObject):
                        text += TJ_sep
                        text += i
                text += "\n"
        return text


class PdfFileReader2(PyPDF2.PdfReader):
    def _flatten(self, pages=None, inherit=None, indirectRef=None):
        inheritablePageAttributes = (
            NameObject("/Resources"), NameObject(
                "/MediaBox"),
            NameObject("/CropBox"), NameObject("/Rotate")
        )
        if inherit == None:
            inherit = dict()
        if pages == None:
            self.flattenedPages = []
            catalog = self.trailer["/Root"].getObject()
            pages = catalog["/Pages"].getObject()

        t = "/Pages"
        if "/Type" in pages:
            t = pages["/Type"]

        if t == "/Pages":
            for attr in inheritablePageAttributes:
                if attr in pages:
                    inherit[attr] = pages[attr]
            for page in pages["/Kids"]:
                addt = {}
                if isinstance(page, IndirectObject):
                    addt["indirectRef"] = page
                self._flatten(page.getObject(), inherit, **addt)
        elif t == "/Page":
            for attr, value in list(inherit.items()):
                # if the page has it's own value, it does not inherit the
                # parent's value:
                if attr not in pages:
                    pages[attr] = value
            pageObj = PageObject2(self, indirectRef)
            pageObj.update(pages)
            self.flattenedPages.append(pageObj)
