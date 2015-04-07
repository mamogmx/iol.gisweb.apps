# -*- coding: utf-8 -*-
from plone import api
from Products.Five.utilities.marker import mark
from .interfaces import IIolDocument, IIolApp
import logging

PROFILE_ID = 'iol.gisweb.apps:default'
logger = logging.getLogger('iol.gisweb.apps')

def initPackage(context):
    try:
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(portal_type='PlominoDatabase')
        for brain in brains:
            db = brain.getObject()
            for doc in db.getAllDocuments():
                if not IIolDocument.providedBy(doc):
                    mark(doc,IIolDocument)
                if not IIolApp.providedBy(doc):
                    mark(doc,IIolApp)
    except:
        pass

