# -*- coding: utf-8 -*-
import os
from zope.interface import Interface, implements, Attribute
from zope.component import adapts
from plone import api
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.CMFPlomino.interfaces import IPlominoDocument, IPlominoForm
from Products.CMFPlone.utils import getToolByName
from zope.component import getGlobalSiteManager
import config
from zope.component import getUtility
from .permissions import IOL_READ_PERMISSION,IOL_EDIT_PERMISSION
from .interfaces import IIolDocument
from .config import USER_CREDITABLE_FIELD,USER_UNIQUE_FIELD,IOL_APPS_FIELD,STATUS_FIELD
from copy import deepcopy
import simplejson as json
from base64 import b64encode
from DateTime import DateTime
import datetime


class IolDocument(object):
    implements(IIolDocument)
    adapts(IPlominoForm,IPlominoDocument)
    tipo_app = u""
    security = ClassSecurityInfo()
    security.declareObjectPublic()
    def __init__(self,obj):
        self.document = obj
        if obj.portal_type == 'PlominoForm':
            tmp = obj.id.split('_')
            if len(tmp) > 2:
                app = tmp[-2]
            else:
                app = config.APP_FIELD_DEFAULT_VALUE
            self.tipo_app = app
        else:
            self.tipo_app = obj.getItem(config.APP_FIELD,config.APP_FIELD_DEFAULT_VALUE)

    security.declarePublic('getIolApp')
    def getIolApp(self):
        return self.tipo_app

    security.declarePublic('verificaRuolo')
    def verificaRuolo(self,ruolo):
        doc = self.document
        pm = api.portal.get().portal_membership
        #pm = getToolByName(self,'portal_membership')
        roles = pm.getAuthenticatedMember().getRolesInContext(doc)
        return ruolo in roles or 'Manager' in roles

    security.declarePublic('getLabels')
    def getLabels(self,field):
        obj = self.document
        db = obj.getParentDatabase()
        forms = db.getForms()
        fld = ''
        for frm in forms:
            if frm.getFormField(field):
                fld = frm.getFormField(field)
        lista = fld.getSettings().getSelectionList(obj)

        label = [i.split('|')[0] for i in lista]
        value = [i.split('|')[1] for i in lista]
        widget = fld.getSettings().widget
        # restuisce un valore testuale
        if widget == 'RADIO':
            if obj.getItem(field)!=None:
                diz={}
                for i,v in enumerate(value):
                    diz[v] = label[i]
                ll=[]

                if obj.getItem(field) in diz.keys():
                    return diz[obj.getItem(field)]
        # restituisce una lista di etichette
        elif widget == 'CHECKBOX':
            if obj.getItem(field)!=None:
                diz={}

                for i,v in enumerate(value):
                    diz[v] = label[i]
                ll=[]
                for i in obj.getItem(field):
                    if i in diz.keys():
                        ll.append(diz[i])
                return ll
        elif widget == 'SELECT':
            if obj.getItem(field)!=None:
                diz={}
                for i,v in enumerate(value):
                    diz[v] = label[i]
                ll=[]
                if isinstance(obj.getItem(field),list):

                    for i in obj.getItem(field):
                        if i in diz.keys():
                            ll.append(diz[i])
                    return ll
                else:
                    return diz[obj.getItem(field)]


    security.declarePublic('sendMail')
    def sendMail(self, Object, msg, To, From='', as_script=False):
        """
        Facility for sending emails using Plone MailHost

        * context: the context (ex. portal) from which get the MailHost
        * msg: dtml type is requested
        * To: the recipient list
        * From: the sender address
        * as_script: if true error message will not be notified through PortalMessage
        """
        doc = self.document
        success = 0

        messages = []
        mail_host = getToolByName(doc, 'MailHost')
        try:
            mail_host.send(msg, To, From or mail_host.getProperty('email_from_address'), Object)
        except Exception as err:
            err_msg = '%s: %s' % (type(err), err)
            err = (unicode(err_msg, errors='replace'), 'error')
            wrn_msg = '''ATTENZIONE! Non e' stato possibile inviare la mail con oggetto: %s''' % Object
            wrn = (unicode(wrn_msg, errors='replace'), 'warning')
            messages.append(err)
            messages.append(wrn)
        else:
            success = 1
            ok_msg = '''La mail con oggetto "%s" e' stata inviata correttamente''' % Object
            ok = (unicode(ok_msg, errors='replace'), 'info')
            messages.append(ok)

        if not as_script:
            plone_tools = getToolByName(doc.getParentDatabase().aq_inner, 'plone_utils')
            for imsg in messages:
                plone_tools.addPortalMessage(*imsg, request=doc.REQUEST)
            return success
        else:
            return dict(success=success, messages=messages)


    security.declarePublic('getFieldValue')
    def getFieldValue(self,field):
        obj = self.document
        db = obj.getParentDatabase()
        form = obj.getForm()
        fld = form.getFormField(field)
        if fld != None:
            adapt = fld.getSettings()
            fieldvalue = adapt.getFieldValue(form, obj)
            return fieldvalue

    security.declareProtected(IOL_READ_PERMISSION,'getIolRoles')
    def getIolRoles(self):
        obj = self.document
        result = dict(
            iol_owner=[],
            iol_viewer=[],
            iol_reviewer = [],
            iol_manager = [],
        )
        for usr,roles in obj.get_local_roles():
            if 'Owner' in roles:
                result['iol_owner'].append(usr)
            if 'iol-viewer' in roles:
                result['iol_viewer'].append(usr)
            if 'iol-reviewer' in roles:
                result['iol_reviewer'].append(usr)
            if 'iol-manager' in roles:
                result['iol_manager'].append(usr)
        return result
    security.declarePublic('updateStatus')
    #security.declareProtected(IOL_READ_PERMISSION,'updateStatus')
    def updateStatus(self):
        obj = self.document
        obj.setItem(STATUS_FIELD,api.content.get_state(obj=obj) )
        db = obj.getParentDatabase()
        # update index
        db.getIndex().indexDocument(obj)
        # update portal_catalog
        if db.getIndexInPortal():
            db.portal_catalog.catalog_object(obj, "/".join(db.getPhysicalPath() + (obj.getId(),)))

    security.declarePublic('isActionSupported')
    def isActionSupported(self, tr=''):
        obj = self.document
        if not tr:
            return False
        wf = getToolByName(self.document, 'portal_workflow')
        for wfname in wf.getChainFor(obj):

            wf = wf.getWorkflowById(wfname)
            if wf.isActionSupported(obj, tr):
                return True
        return False

    security.declarePublic('wfState')
    def wfState(self):
        wf = getToolByName(self.document, 'portal_workflow')
        return wf.getInfoFor(self.document, 'review_state')



    security.declareProtected(IOL_READ_PERMISSION,'wfInfo')
    def wfInfo(self,):
        obj = self.document
        result = dict(
            wf_chain=list(),
            wf_state='',
            wf_variables=dict(),
            wf_actions=list(),
            wf_history=list(),
        )
        wftool = getToolByName(obj, 'portal_workflow')

        result['wf_state'] = self.wfState()

        for wf_id in wftool.getChainFor(obj):
            result['wf_chain'].append(wf_id)

        for wf_var in wftool.getCatalogVariablesFor(obj):
            result['wf_variables'][wf_var] = wftool.getInfoFor(obj, wf_var, default='')

        result['wf_actions'] = [dict(id=res['id'],title=res['name'],url=res['url']) for res in wftool.listActions(object=obj)]

        result['wf_history'] = wftool.getInfoFor(obj, 'review_history', default=[])
        return result

    security.declareProtected(IOL_READ_PERMISSION,'getInfoFor')
    def getInfoFor(self,info,wf_id=''):
        obj = self.document
        wf = getToolByName(obj, 'portal_workflow')
        return wf.getInfoFor(obj,info,default='')

    security.declarePublic('getDatagridValue')
    def getDatagridValue(self,field='',form=''):
        doc = self.document
        db = doc.getParentDatabase()
        if form:
            frm = db.getForm(form)
        else:
            frm = doc.getForm()
        fld = frm.getFormField(field)
        elenco_fields = fld.getSettings().field_mapping
        lista_fields = elenco_fields.split(',')


        diz_tot=[]
        for idx,itm in enumerate(doc.getItem(field)):
            diz = {}
            for k,v in enumerate(lista_fields):
                diz[v] = doc.getItem(field)[idx][k]
            diz_tot.append(diz)
        return diz_tot

    # method to get info on attachment field
    security.declarePublic('getAttachmentInfo')
    def getAttachmentInfo(self, field=''):
        doc = self.document
        result = list()
        files_list = doc.getItem(field, None)
        if files_list and type(files_list) == type(dict()):
            for k, v in files_list.items():

                f = doc.getfile(k, asFile=True)
                size = f.get_size()
                mime = f.getContentType()
    # TODO select correct icon basing on mimetype
                file_info = dict(
                    name=k,
                    mimetype=mime,
                    size=size,
                    url="%s/%s" % (doc.absolute_url(), k),
                    icon="",
                    b64file=b64encode(f.__str__())
                )
                result.append(file_info)

        return result
    # Assign selected user to Iol Groups
    def _assignGroups(self,obj,username,grps):
        portal_groups = getToolByName(obj, 'portal_groups')
        for grp in grps:
            portal_groups.addPrincipalToGroup(username, grp)

    # remove selected user from groups
    def _removeGroups(self,obj,username,grps):
        portal_groups = getToolByName(obj, 'portal_groups')
        for grp in grps:
            portal_groups.removePrincipalFromGroup(username, grp)

    #Assign ownership to selected user
    def _assignOwner(self,obj,user,add=True):
        if add:
            username = user.getUserName()
            obj.manage_setLocalRoles(username, ["Owner",])
        else:
            obj.changeOwnership(user)
        obj.reindexObjectSecurity()

     #Procedure that search all documents of the selected user, assign him ownership, and move him in iol groups
    security.declarePublic('accreditaUtente')
    def accreditaUtente(self):
        obj = self.document
        user = obj.getOwner()
        username = user.getUserName()
        apps = obj.getItem(IOL_APPS_FIELD,[])

        #for appName in apps:
            #app = App(appName)
            #for grp in app.getOwnerGroups():
            #    self._assignGroups(obj,username,[grp])

        self._assignGroups(obj,username,apps)

        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(portal_type='PlominoDatabase')
        unique = obj.getItem(USER_UNIQUE_FIELD,'')
        cont = 0
        brains = []
        for brain in brains:
            db = brain.getObject()
            idx = db.getIndex()
            req = dict(USER_CREDITABLE_FIELD = unique)
            for br in idx.dbsearch(req,only_allowed=False):
                doc = br.getObject()
                self._assignOwner(doc,user)

                cont += 1
        return cont

    security.declarePublic('revocaUtente')
    def revocaUtente(self):
        obj = self.document
        user = obj.getOwner()
        username = user.getUserName()
        apps = obj.getItem(IOL_APPS_FIELD,[])
        self._removeGroups(obj,username,apps)


    def _serialDatagridItem(doc, obj ):
        result = list()
        itemvalue = doc.getItem(obj['name'])
        for el in itemvalue:
            i = 0
            res = dict()
            for fld in obj['field_list']:
                res[fld]= el[i]
                i+=1
            result.append(res)
        return result



    security.declarePublic('serializeDoc')
    def serializeDoc(self):
        doc = self.document
        results = dict(deepcopy(doc.items))
        frm = doc.getForm()
        fieldnames = []
        for i in frm.getFormFields(includesubforms=True, doc=None, applyhidewhen=False):
            if i.getFieldType()=='DATAGRID':
                fieldnames.append(dict(field=i,name=i.getId(),form=i.getSettings().associated_form,field_list=i.getSettings().field_mapping.split(',')))
        try:
            for f in fieldnames:
                if f['name'] in results:
                    del results[f['name']]
                results[f['name']]=self._serialDatagridItem(doc,f)
        except:
            results[f['name']]= []
            api.portal.show_message(message='Errore nel campo %s' %f['name'], request=doc.REQUEST)
        return results
    security.declarePublic('docToJson')
    def docToJson(self):
        return json.dumps(self.serializeDoc(),default=DateTime.DateTime.ISO,use_decimal=True)


    security.declarePublic('renderSimpleValue')
    def renderSimpleValue(self,itemvalue,field,fieldtype):
        doc = self.document
        db = doc.getParentDatabase()
        if not fieldtype:
            fieldtype = field.getFieldType()
        renderedValue = None
        if itemvalue and field:

            if fieldtype == 'SELECTION':

                nfo = dict([i.split('|')[::-1] for i in field.getSettings().getSelectionList(doc)])

                if isinstance(itemvalue, basestring):
                    renderedValue = nfo.get(itemvalue) or itemvalue
                elif isinstance(itemvalue[0], dict):
                    import pdb; pdb.set_trace()
                    renderedValue = [i.keys() for i in itemvalue]
                else:
                    renderedValue = [(nfo.get(i) or i) for i in itemvalue]
            elif fieldtype not in ('TEXT', 'NUMBER', ):
            # not worth it to call the template to render text and numbers
            # it is an expensive operation
                fieldtemplate = db.getRenderingTemplate('%sFieldRead' % fieldtype) \
                    or db.getRenderingTemplate('DefaultFieldRead')
                renderedValue = fieldtemplate(fieldname=field.getId(),
                    fieldvalue = itemvalue,
                    selection = field.getSettings().getSelectionList(doc),
                    field = field,
                    doc = doc
                ).strip()

        if renderedValue == None:
            if not itemvalue:
                renderedValue = ''
            elif fieldtype == 'TEXT':
                renderedValue = itemvalue
            elif fieldtype == 'NUMBER':
                custom_format = None if not field else field.getSettings('format')
                renderedValue = str(itemvalue) if not custom_format else custom_format % itemvalue
            elif fieldtype == 'DATETIME':
                if field:
                    custom_format = field.getSettings('format') or db.getDateTimeFormat()
                else:
                    custom_format = db.getDateTimeFormat()
                try:
                    renderedValue = itemvalue.strftime(custom_format)
                except:
                    renderedValue = itemvalue
            else:
                try:
                    json.dumps(itemvalue)
                except TypeError:
                    renderedValue = u'%s' % itemvalue
                else:
                    renderedValue = itemvalue
        return renderedValue









    #Returns a list of 2-tuples with the data contained in the document item
    security.declarePublic('serialItem')
    def  serialItem(self, name, fieldnames = [],fieldsubset = [],fieldsremove=[]):
        doc = self.document
        db = doc.getParentDatabase()
        result = list()
        itemvalue = doc.getItem(name)
        if itemvalue == '':
            self.getFieldValue(name)
        form = doc.getForm()
        if not fieldnames:
            fieldnames = [i.getId() for i in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False)]
        if name in fieldnames:
            field = form.getFormField(name)
            fieldtype = field.getFieldType()
        else:
            field = None
        if isinstance(itemvalue, (int, float, )):
            fieldtype = 'NUMBER'
        elif isinstance(itemvalue, DateTime):
            fieldtype = 'DATETIME'
        elif isinstance(itemvalue,list):
            fieldtype = 'SELECTION'
        else:
            fieldtype = 'TEXT'
        assert fieldtype, 'No fieldtype is specified for "%(name)s" with value "%(itemvalue)s"' % locals()

        # arbitrary assumption
        if fieldtype == 'DATE':
            fieldtype = 'DATETIME'
        if fieldtype == 'DATAGRID' or (fieldtype == 'DOCLINK'):
            sub_result = list()
            if fieldtype == 'DATAGRID':
                grid_form = db.getForm(field.getSettings().associated_form)
                grid_field_names = field.getSettings().field_mapping.split(',')
            for innervalue in itemvalue or []:
                if fieldtype == 'DOCLINK':
                    sub_doc = db.getDocument(innervalue)
                    sub_element = dict(self.serialDoc(fieldsubset=fieldsubset,fieldsremove=fieldsremove,doc=sub_doc))
                else:
                    sub_element = dict([(k, self.renderSimpleValue(v, grid_form.getFormField(k))) for k,v in zip(grid_field_names, innervalue)])
                sub_result.append(sub_element)
            result.append((name, sub_result))
        else:
            renderedValue = self.renderSimpleValue(itemvalue,field,fieldtype)
            result.append((name, renderedValue))
        return result


    security.declarePublic('serialDoc')
    def serialDoc(self,fieldsubset='',fieldsremove='',doc=''):
        if doc == '':
            doc = self.document

        db = doc.getParentDatabase()

        form = doc.getForm()
        fieldnames = [i.getId() for i in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False)]
        contentKeys = fieldnames + [i for i in doc.getItems() if i not in fieldnames]
        if fieldsubset and isinstance(fieldsubset, basestring):
            fieldsubset = fieldsubset.split(',')
        if fieldsremove and isinstance(fieldsremove, basestring):
            fieldsremove = fieldsremove.split(',')

        if fieldsubset:
            contentKeys = [i for i in contentKeys  if i in fieldsubset]
        if fieldsremove:
            contentKeys = [i for i in contentKeys if i not in fieldsremove]


        result = []
        for key in contentKeys:
            result += self.serialItem(key,fieldnames=fieldnames,fieldsubset=fieldsubset,fieldsremove=fieldsremove)

        # Output rendering
        if format == 'json':
            doc.REQUEST.RESPONSE.setHeader("Content-type", "application/json")
            return json.dumps(dict(result))
        elif format == 'xml':
            assert GOT_XML, '%s' % err
            doc.REQUEST.RESPONSE.setHeader("Content-type", "text/xml")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + dict2xml(dict(info=dict(result)))
        else:
            return result

InitializeClass(IolDocument)

