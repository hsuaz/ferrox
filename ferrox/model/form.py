import ferrox.model as model

import formencode
from formencode import validators
import urllib

class FileUploadValidator(validators.FancyValidator):
    def _to_python(self, value, state):
        filename = value.filename
        content = value.value
        return dict(filename=filename, content=content)

class UniqueUsername(formencode.FancyValidator):
    def _to_python(self, value, state):
        users_q = model.Session.query(model.User).filter_by(username = value)
        if users_q.count() > 0:
            raise formencode.Invalid('That username already exists', value, state)
        else:
            return value

class Recaptcha(validators.FormValidator):
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
        recaptcha_url = 'http://api-verify.recaptcha.net/verify?' + urllib.urlencode(recaptcha_args)
        recaptcha_response = urllib.urlopen(recaptcha_url)
        response_lines =  recaptcha_response.readlines()
        error = {'recaptcha': formencode.Invalid(self.fail_message, field_dict, state)}
        if response_lines[0] != 'true\n':
            raise formencode.Invalid(self.fail_message, field_dict, state, error_dict = error)

class ExistingUserValidator(formencode.FancyValidator):
    def _to_python(self, value, state):
        return model.User.get_by_name(value)

    def validate_python(self, value, state):
        if value == None:
            raise formencode.Invalid('No such user', value, state)

class PrimaryKeyValidator(formencode.FancyValidator):
    def _to_python(self, value, state):
        try:
            return model.Session.query(self.table).filter_by(id=value).one()
        except InvalidRequestError:
            return None

    def validate_python(self, value, state):
        if value == None:
            raise formencode.Invalid('Invalid id', value, state)

class RegisterForm(formencode.Schema):
    username = formencode.All(validators.PlainText(not_empty = True),
                              UniqueUsername)
    email = validators.Email(not_empty = True)
    email_confirm = validators.String()
    password = validators.String(not_empty = True)
    password_confirm = validators.String()
    TOS_accept = validators.OneOf(['1'])
    chained_validators = [validators.FieldsMatch('email', 'email_confirm'),
                          validators.FieldsMatch('password', 'password_confirm'),]

class LoginForm(formencode.Schema):
    username = validators.PlainText(not_empty=True)
    password = validators.PlainText(not_empty=True)

class NewsForm(formencode.Schema):
    title = validators.NotEmpty()
    content = validators.NotEmpty()
    is_anonymous = validators.Bool()
    avatar_id = validators.Int()

class SubmitEditForm(formencode.Schema):
    fullfile = FileUploadValidator()
    halffile = FileUploadValidator()
    thumbfile = FileUploadValidator()
    title = formencode.validators.String(not_empty=True)
    tags = formencode.validators.String(not_empty=True)
    description = formencode.validators.NotEmpty(not_empty=True)
    avatar_id = validators.Int()

class SubmitForm(SubmitEditForm):
    fullfile = FileUploadValidator(not_empty=True)

class EditForm(SubmitEditForm):
    fullfile = FileUploadValidator()

class JournalForm(formencode.Schema):
    title = validators.String(not_empty=True)
    content = validators.NotEmpty(not_empty=True)
    avatar_id = validators.Int()

class DeleteForm(formencode.Schema):
    public_reason = formencode.validators.PlainText(not_empty=True)
    private_reason = formencode.validators.PlainText(not_empty=False, if_empty=u'')
    confirm = formencode.validators.PlainText(not_empty=False, if_missing=None)
    cancel = formencode.validators.PlainText(not_empty=False, if_missing=None)

class SearchForm(formencode.Schema):
    query_tags = formencode.validators.NotEmpty(not_empty=False, if_missing='')
    query_main = formencode.validators.NotEmpty(not_empty=True)
    query_author = formencode.validators.PlainText(not_empty=False, if_missing='')
    search_for = formencode.validators.PlainText()
    search_title = formencode.validators.Bool()
    search_description = formencode.validators.Bool()
    page = formencode.validators.Int(not_empty=False, if_missing=1)
    perpage = formencode.validators.Int(not_empty=False, if_missing=0)

class TagFilterForm(formencode.Schema):
    tags = formencode.validators.NotEmpty(not_empty=False, if_missing='')
    page = formencode.validators.Int(not_empty=False, if_missing=None)
    perpage = formencode.validators.Int(not_empty=False, if_missing=None)

class ReplyValidator(validators.FormValidator):
    validate_partial_form = True

    def validate_partial(self, value, state):
        value.has_key('recipient')
        return

class SendNoteForm(formencode.Schema):
    subject = validators.String(not_empty=True)
    content = validators.String(not_empty=True)

    def _to_python(self, value, state=None):
        if 'reply_to_note' in value:
            self.fields['reply_to_note'] = formencode.All(
                validators.String(not_empty=True),
                PrimaryKeyValidator(table=model.Note)
                )

        else:
            self.fields['recipient'] = formencode.All(
                validators.String(not_empty=True),
                ExistingUserValidator()
                )

        return formencode.Schema._to_python(self, value, state)

class CommentForm(formencode.Schema):
    title = validators.String(if_empty='(no subject)')
    content = validators.String(not_empty=True)

class WatchForm(formencode.Schema):
    journals = validators.Bool(if_empty=True, if_missing=False)
    submissions =validators.Bool(if_empty=True, if_missing=False) 

class MemberListPagingForm(formencode.Schema):
    page = formencode.validators.Int(not_empty=False, if_missing=0)
    perpage = formencode.validators.Int(not_empty=False, if_missing=0)


class AvatarForm(formencode.Schema):
    avatar = FileUploadValidator(not_empty=False, if_missing=None)
    title = formencode.validators.String(not_empty=False, if_missing=None)
    default = validators.Bool(if_empty=True, if_missing=False)
    #delete = formencode.validators.Int(repeating=True)
    #delete = formencode.ForEach(formencode.All(formencode.validators.Int()))

class BanForm(formencode.Schema):
    username = ExistingUserValidator()
    expiration = formencode.validators.DateConverter()
    role_id = PrimaryKeyValidator(table=model.Role)
    reason = formencode.validators.String(not_empty=True)
    notes = formencode.validators.String(not_empty=False, if_missing="")

