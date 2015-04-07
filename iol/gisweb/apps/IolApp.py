# -*- coding: utf-8 -*-
from zope.interface import Interface, implements, Attribute
from zope.component import adapts
import os
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.CMFPlomino.interfaces import IPlominoDocument, IPlominoForm
from zope.component import getGlobalSiteManager
from iol.gisweb.utils import config
from gisweb.iol.permissions import IOL_READ_PERMISSION, IOL_EDIT_PERMISSION, IOL_REMOVE_PERMISSION
from zope.component import getUtility,queryUtility
from .interfaces import IIolApp, IolDocument

from iol.gisweb.utils import loadJsonFile,dateEncoder


class IolApp(object):
    implements(IIolApp)
    adapts(IPlominoForm, IPlominoDocument)
    tipo_app = u""
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self, obj):
        self.document = obj
        iDoc = IolDocument(obj)
        self.tipo_app = iDoc.getIolApp()
        self.path = os.path.dirname(os.path.abspath(__file__))

    security.declarePublic('NuovoNumeroPratica')
    def NuovoNumeroPratica(self):

        utils = queryUtility(IIolApp,name=self.tipo_app, default=config.APP_FIELD_DEFAULT_VALUE)
        if not 'NuovoNumeroPratica' in dir(utils):
            utils = getUtility(IIolApp,config.APP_FIELD_DEFAULT_VALUE)
        return utils.NuovoNumeroPratica(self.document)

    security.declarePublic('invioPraticaweb')
    def invioPraticaweb(self):
        utils = queryUtility(IIolApp,name=self.tipo_app, default=config.APP_FIELD_DEFAULT_VALUE)
        if not 'invioPraticaweb' in dir(utils):
            utils = getUtility(IIolApp,config.APP_FIELD_DEFAULT_VALUE)        
        return utils.invioPraticaweb(self.document)

    security.declarePublic('accreditaUtente')
    def accreditaUtente(self):
        utils = queryUtility(IIolApp,name=self.tipo_app, default=config.APP_FIELD_DEFAULT_VALUE)
        if not 'accreditaUtente' in dir(utils):
            utils = getUtility(IIolApp,config.APP_FIELD_DEFAULT_VALUE)        
        return utils.accreditaUtente(self.document)


    security.declarePublic('createPdf')
    def createPdf(self,filename,itemname='documento_da_firmare',overwrite=False):
        utils = queryUtility(IIolApp,name=self.tipo_app, default=config.APP_FIELD_DEFAULT_VALUE)
        if not 'createPdf' in dir(utils):
            utils = getUtility(IIolApp,config.APP_FIELD_DEFAULT_VALUE)        
        return utils.createPdf(self.document,filename,itemname,overwrite)
    
    security.declarePublic('getConvData')
    def getConvData(self,json_data):
        utils = getUtility(IIolApp,'default')
        return utils.getConvData(json_data)

    security.declarePublic('sendThisMail')
    def sendThisMail(self,ObjectId,sender='',debug=0,To='',password=''):               
        utils = getUtility(IIolApp,self.tipo_app)        
        return utils.sendThisMail(self.document,ObjectId,sender,debug,To,password)      

    security.declarePublic('updateStatus')
    def updateStatus(self):
        utils = queryUtility(IIolApp,name=self.tipo_app, default=config.APP_FIELD_DEFAULT_VALUE)
        if not 'updateStatus' in dir(utils):
            utils = getUtility(IIolApp,config.APP_FIELD_DEFAULT_VALUE)
        return utils.updateStatus(self.document)

    security.declarePublic('reindex_doc')
    def reindex_doc(self):
        utils = queryUtility(IIolApp,name=self.tipo_app, default=config.APP_FIELD_DEFAULT_VALUE)
        if not 'reindex_doc' in dir(utils):
            utils = getUtility(IIolApp,config.APP_FIELD_DEFAULT_VALUE)
        return utils.reindex_doc(self.document) 

    # Wizard Info
    security.declarePublic('getWizardInfo')

    def getWizardInfo(self):
        doc = self.document
        # Inizializzo il risultato
        result = dict(
            actions=[],
            state="",
            base_url="%s/content_status_modify?workflow_action=" % (doc.absolute_url()),
            forms=[]
        )
        #Istanzio l'oggetto IolDocument

        iDoc = IolDocument(doc)
        info = loadJsonFile("%s/applications/wizard_info/%s.json" % (self.path, self.tipo_app)).result

        wfInfo = iDoc.wfInfo()
        if doc.portal_type == 'PlominoForm':
            result["state"] = info["initial_state"]
            result["actions"] = info["initial_actions"]
        else:
            result["state"] = wfInfo["wf_state"]
            result["actions"] = wfInfo["wf_actions"]
        for v in info["states"]:
            cls_list = list()
            if not iDoc.isActionSupported(v["action"]):
                cls_list.append('link-disabled')
                action = ""
            else:
                action = v["action"]
            if result["state"] == v["state"]:
                cls_list.append("active")

            i = {"label": v["label"], "class": " ".join(cls_list), "action": action}
            result["forms"].append(i)
        return result

InitializeClass(IolApp)