import requests
from settings import CANVAS_API_KEY as api_key, CANVAS_API_URL as web_url


access_token = "?access_token=%s" % (api_key)
base_url = "%sapi/v1/" % (web_url)


class DataObject(object):
    """
    Initiate the DataObject class, allow it to take any number of params
    as long as they are paired with a keyword. The keyword for that param
    becomes the same as the one given.
    """
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])


class WebcourseObject(object):
    """
    Create an object to handle calls to webcourses.
    get_courses looks for the response status_code 200
    to verify connection is made
    get_courses() returns a list of the courses with:
    name - for display
    id - for reference in creating modules
    """
    def __init__(self):
        self.errors = False
        # return array of Course objects
        self.course_list = self.get_courses()

    def get_courses(self):
        course_list = []
        url = "%scourses/%s" % (base_url, access_token)
        response = requests.get(url)  # look into prepared response?
        if response.status_code == 200:
            for item in response.json():
                # response.json() is a list of json objects
                this_course = Course(
                    name=item['name'],
                    cid=item['id'])
                course_list.append(this_course)
        else:
            self.errors = True
            self.code = response.status_code
        return course_list


class Course(DataObject):
    """
    A course object has a name and an id.
    get_modules() returns a list of modules.
    The returned modules have:
    name - for display
    id - for reference in creating items
    items_url - for listing all the items in a module
    cid - Course ID
    """
    # A course has a name, id, and list of modules
    @property
    def modules(self):
        if not hasattr(self, '_modules'):
            return None
        return self._modules

    def get_modules(self):
        module_list = []
        url = "%scourses/%s/modules%s" % (base_url, self.cid, access_token)
        response = requests.get(url)
        for item in response.json():
            this_module = Module(
                name=item['name'],
                mid=item['id'],
                items_url=item['items_url'],
                cid=self.cid)
            module_list.append(this_module)

        return module_list

    def get_name(self):
        return self.name

    def __unicode__(self):
        return self.name

    def __str__(self):
        return "[{0}] {1}".format(self.id, self.name)

    def __repr__(self):
        return "[{0}] {1}".format(self.id, self.name)


class Module(DataObject):
    """
    A module has a name, id, and items_url. It generates CourseItems
    """

    def get_module_items(self):  # return a list of items in module
        item_list = []
        url = "%scourses/%s/modules/%s/items%s" % (
            base_url, self.cid, self.mid, access_token)
        response = requests.get(url)

        for item in response.json():
            if item['type'] == 'File' or item['type'] == 'Page':
                this_item = CourseItem(
                    title=item['title'],
                    id=item['id'],
                    type=item['type'],
                    url=item['url'])
                item_list.append(this_item)
        return item_list

    def __str__(self):
        return '[{0}] {1}'.format(self.id, self.name)

    def __repr__(self):
        return '[{0}] {1}'.format(self.id, self.name)


class CourseItem(DataObject):
    """
    A CourseItem has a type and name.
    A Canvas Wiki Page also had a 'body', we use the url
    as the 'filename' property
    A File has a 'filename', 'content_type', 'url'
        'thumbnail_url' and 'size'.
    The thumbnail and size are not yet utilized.
    from_url uses 'cls' to reference class information
    """

    def __str__(self):
        return '[{0}] {1}'.format(self.type, self.name)

    @classmethod
    def from_url(cls, url, expect_json=True):

        response = requests.get(url + access_token)

        if expect_json:
            data = response.json()
        else:
            data = {'raw': response.content()}

        params = {}
        if 'body' in data:
            params['type'] = 'page'
            params['name'] = data['title']
            params['body'] = data['body']
            params['filename'] = data['url']
        else:
            params['type'] = 'file'
            params['name'] = data['display_name']
            params['filename'] = data['filename']
            params['content_type'] = data['content-type']
            params['url'] = data['url']
            params['thumbnail_url'] = data['thumbnail_url']
            params['size'] = data['size']

        return cls(**params)

    @property
    def html(self):
        html_template = unicode((
            '<!doctype html>'
            '<html lang="en">'
            '    <head>'
            '        <meta charset="utf-8">'
            '        <title>{title}</title>'
            '    </head>'
            '    {body}'
            '</html>'),
            encoding='utf-8'
        )
        if not hasattr(self, '_html'):
            if not hasattr(self, 'body'):
                raise ValueError('missing body attirubte for html')
            if not hasattr(self, 'name'):
                raise ValueError('missing name attirubte of html')
            self._html = html_template.format(
                title=self.name,
                body=self.body
            )
        return self._html

    @property
    def file_path(self):
        if not hasattr(self, '_file_path'):
            if self.type == 'page':
                self._file_path = 'files/{0}.html'.format(self.name)
            else:
                self._file_path = 'files/{0}'.format(self.filename)

        return self._file_path

    def item_content(self, cache=False):
        if self.type == 'page':
            content = self.html.encode('utf-8')
        elif hasattr(self, '_raw'):
            content = self._raw
        else:
            response = requests.get(self.url)
            if cache is True:
                self._raw = response.content
            content = response.content
        return content
