import formencode
import furaffinity.model as model
import urllib

class FileUploadValidator(formencode.validators.FancyValidator):
    def _to_python(self, value, state):
        filename = value.filename
        content = value.value
        return dict(filename=filename,content=content)

class UniqueUsername(formencode.FancyValidator):
    def _to_python(self, value, state):
        users_q = model.Session.query(model.User).filter_by(username = value)
        if users_q.count() > 0:
            raise formencode.Invalid('That username already exists', value, state)
        else:
            return value


class Recaptcha(formencode.validators.FormValidator):
    validate_partial_form = True
    
    fail_message = 'Recaptcha failed'

    def validate_partial(self, field_dict, state):
        captcha_fields = ['remote_addr', 
                          'recaptcha_challenge_field', 
                          'recaptcha_response_field']
        for name in captcha_fields:
            if not field_dict.has_key(name):
                return
        self.validate_python(field_dict, state)

    def validate_python(self, field_dict, state):
        recaptcha_args = {'privatekey': '6LcAvAAAAAAAAHfE6nROKB8EKqsF5mUz1jmRNaqm',
                          'remoteip': field_dict['remote_addr'],
                          'challenge': field_dict['recaptcha_challenge_field'],
                          'response': field_dict['recaptcha_response_field']}
        recaptcha_response = urllib.urlopen('http://api-verify.recaptcha.net/verify', urllib.urlencode(recaptcha_args))
        response_lines =  recaptcha_response.readlines()
        error = {'recaptcha': formencode.Invalid(self.fail_message, field_dict, state)}
        if response_lines[0] != 'true\n':
            raise formencode.Invalid(self.fail_message, field_dict, state, error_dict = error)
        

class RegisterForm(formencode.Schema):
    username = formencode.All(formencode.validators.PlainText(not_empty = True),
                              UniqueUsername)
    email = formencode.validators.Email(not_empty = True)
    email_confirm = formencode.validators.String()
    password = formencode.validators.String(not_empty = True)
    password_confirm = formencode.validators.String()
    commit = formencode.validators.PlainText(not_empty=False)
    remote_addr = formencode.validators.String(not_empty = True)
    recaptcha_challenge_field = formencode.validators.String(not_empty = True)
    recaptcha_response_field = formencode.validators.String(not_empty = True)
    TOS_accept = formencode.validators.OneOf(['1'])
    chained_validators = [formencode.validators.FieldsMatch('email', 'email_confirm'),
                          formencode.validators.FieldsMatch('password', 'password_confirm'),
                          Recaptcha()]

class LoginForm(formencode.Schema):
    username = formencode.validators.PlainText(not_empty=True)
    password = formencode.validators.PlainText(not_empty=True)
    commit = formencode.validators.PlainText(not_empty=True)
    
class NewsForm(formencode.Schema):
    title = formencode.validators.NotEmpty()
    content = formencode.validators.NotEmpty()
    is_anonymous = formencode.validators.Bool()
    commit = formencode.validators.PlainText(not_empty=True)

class SubmitForm(formencode.Schema):
    fullfile = FileUploadValidator()
    halffile = FileUploadValidator()
    thumbfile = FileUploadValidator()
    title = formencode.validators.String(not_empty=True)
    tags = formencode.validators.String(not_empty=True)
    description = formencode.validators.NotEmpty(not_empty=True)
    commit = formencode.validators.PlainText(not_empty=False)


class JournalForm(formencode.Schema):
    title = formencode.validators.String(not_empty=True)
    content = formencode.validators.NotEmpty(not_empty=True)
    commit = formencode.validators.PlainText(not_empty=False)

class DeleteForm(formencode.Schema):
    confirm = formencode.validators.PlainText(not_empty=False, if_missing=None)
    cancel = formencode.validators.PlainText(not_empty=False, if_missing=None)

class SearchForm(formencode.Schema):
    query_tags = formencode.validators.NotEmpty(not_empty=False)
    query_main = formencode.validators.NotEmpty(not_empty=True)
    query_author = formencode.validators.PlainText(not_empty=False)
    search_submissions = formencode.validators.Bool()
    search_journals = formencode.validators.Bool()
    search_news = formencode.validators.Bool()
    search_title = formencode.validators.Bool()
    search_description = formencode.validators.Bool()
    commit = formencode.validators.PlainText(not_empty=False)
