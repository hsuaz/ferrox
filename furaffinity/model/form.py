import formencode

class FileUploadValidator(formencode.validators.FancyValidator):
    def _to_python(self, value, state):
        filename = value.filename
        content = value.value
        return dict(filename=filename,content=content)

class RegisterForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    username = formencode.validators.PlainText(not_empty=True)
    email = formencode.validators.Email(not_empty=True)
    email_confirm = formencode.validators.Email(not_empty=True)
    password = formencode.validators.PlainText(not_empty=True)
    password_confirm = formencode.validators.PlainText(not_empty=True)
    tos = formencode.validators.Bool(not_empty=True)
    chained_validators = [formencode.validators.FieldsMatch('email', 'email_confirm'),
            formencode.validators.FieldsMatch('password', 'password_confirm')]

class LoginForm(formencode.Schema):
    username = formencode.validators.PlainText(not_empty=True)
    password = formencode.validators.PlainText(not_empty=True)
    commit = formencode.validators.PlainText(not_empty=True)

class SubmitForm(formencode.Schema):
    fullfile = FileUploadValidator(not_empty=True)
    thumbfile = FileUploadValidator()
    type = formencode.validators.PlainText(not_empty=False)
    title = formencode.validators.String(not_empty=True)
    description = formencode.validators.NotEmpty(not_empty=True)
    commit = formencode.validators.PlainText(not_empty=False)

