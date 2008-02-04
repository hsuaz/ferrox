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
