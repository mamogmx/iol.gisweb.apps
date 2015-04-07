from plone import api
from ..IolDocument import IolDocument
import simplejson as json
import DateTime



# Get Iol Role on Object
class getIolRoles(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        doc = self.aq_parent
        iDoc = IolDocument(doc)
        return iDoc.getIolRoles()

# Retrieve Objects's WorkFlow Info
class wfInfo(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        doc = self.aq_parent
        iDoc = IolDocument(doc)
        doc.REQUEST.RESPONSE.headers['Content-Type'] = 'application/json'
        data = iDoc.wfInfo()
        return json.dumps(data,default=DateTime.DateTime.ISO,use_decimal=True)


# Get Workflow State
class getState(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        doc = self.aq_parent
        return api.content.get_state(obj=doc)

# List of all available Transition
class wfTransitions(object):

    def __init__(self,context,request):
        self.context = context
        self.request = request

    def __call__(self):
        doc = self.aq_parent
        if doc.portal_type == 'PlominoForm':
            return []
        iDoc = IolDocument(doc)
        data = iDoc.wfInfo()
        result = list()
        for act in data['wf_actions']:
            result.append(act['id'])
        return result



class nextNumber(object):

    def __init__(self,context,request):
        self.context = context
        self.request = request

    def __call__(self,field='numero_pratica'):
        return ""

class createDocx(object):

    def __init__(self,context,request):
        self.context = context
        self.request = request

    def __call__(self):
        return ""

class getLabels(object):

    def __init__(self,context,request):
        self.context = context
        self.request = request

    def __call__(self,field):
        doc = self.aq_parent
        iDoc = IolDocument(doc)
        return iDoc.getLabels(field)

class getFieldValue(object):

    def __init__(self,context,request):
        self.context = context
        self.request = request

    def __call__(self,field):
        doc = self.aq_parent
        iDoc = IolDocument(doc)
        return iDoc.getFieldValue(field)

class frmFields(object):

    def __init__(self,context,request):
        self.context = context
        self.request = request

    def __call__(self):
        frm = self.aq_parent
        result = dict()
        r = dict()
        fields=[dict(fieldid = f.id,form=f.aq_parent.id,fieldtype = f.FieldType) for f in frm.getFormFields(includesubforms=True)]
        for f in fields:
            if not f['form'] in result.keys():
                result[f['form']] = dict()
            result[f['form']][f['fieldid']] = f
        rkeys = sorted(result)
        for i in rkeys:
            rrkeys = sorted(result[i])
            r[i] = dict()
            for j in rrkeys:
                r[i][j] = result[i][j]


        self.request.RESPONSE.headers["content-type"]="application-json"
        return json.dumps(r)

#class serialDoc(object):

#    def __init__(self,context,request):
#        self.context = context
#        self.request = request

#    def __call__(self,fieldsubset='',fieldsremove='',doc=''):
#        doc = self.aq_parent
#        iDoc = IolDocument(doc)
#        return iDoc.serialDoc(fieldsubset='',fieldsremove='',doc='')  