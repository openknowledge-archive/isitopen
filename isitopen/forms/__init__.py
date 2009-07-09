import formalchemy.forms
import isitopen.model as model

# Does not seem to be needed, FA generates them for itself!
Message = formalchemy.forms.FieldSet(model.Message)
Enquiry = formalchemy.forms.FieldSet(model.Enquiry)
User = formalchemy.forms.FieldSet(model.Enquiry)

