
from celery import shared_task
from .models import Document

import easyocr
from pdf2image import convert_from_path
import xmlrpc.client
import logging

_logger = logging.getLogger(__name__)


@shared_task
def process_ocr():
    docs = Document.objects.filter(ocr_processed=False)
    _logger.info('=======Process OCR Task========')
    buffer_image = '/code/rest/mediafiles/buffer.jpg'
    for doc in docs:
        path = doc.file.path
        text = ''
        reader = easyocr.Reader(lang_list=['en', 'de'])
        if doc.file:
            if doc.mimetype == 'application/pdf':
                pages = convert_from_path(path, 500)
                _logger.info('Doc %s:%s pages:%s' %
                             (doc.name, path, len(pages)))
                for page in pages:
                    page.save(buffer_image, 'JPEG')
                    data = reader.readtext(buffer_image)
                    for element in data:
                        text += element[1]+' '
            elif doc.mimetype in ['image/jpeg', 'image/png']:
                data = reader.readtext(path)
                for element in data:
                    text += element[1]+' '
        if text:
            doc.text = text
        doc.ocr_processed = True
        doc.save()
    _logger.info('=======End Process OCR Task========')


@shared_task
def process_odoo():
    docs = Document.objects.filter(ocr_processed=True,
                                   odoo_sent=False, odoo_id__gt=0)
    _logger.info('=======Process Odoo Task========')
    url = 'http://host.docker.internal:8069'
    user = 'admin'
    password = 'admin'
    db = 'Agustin'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, user, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    for doc in docs:
        models.execute_kw(db, uid, password, 'documents.document', 'write', [[doc.odoo_id], {
            'ocr_text': doc.text
        }])
        doc.odoo_sent = True
        doc.save()
    _logger.info('=======End Odoo Process Task========')
