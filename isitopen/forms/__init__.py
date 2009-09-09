import formalchemy.forms
import formalchemy.fields
import isitopen.model as model

class OurFieldSet(formalchemy.forms.FieldSet):
    pass

OurFieldSet.default_renderers[model.JsonType] = formalchemy.fields.TextFieldRenderer

# Does not seem to be needed, FA generates them for itself!
Message = OurFieldSet(model.Message)
Enquiry = OurFieldSet(model.Enquiry)
User = OurFieldSet(model.Enquiry)

