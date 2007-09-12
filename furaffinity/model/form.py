import formencode

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
