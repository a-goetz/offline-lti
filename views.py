from flask import Flask, render_template, session, request, Response
from zipfile import ZipFile
from pylti.flask import lti
import logging
import json
from logging.handlers import RotatingFileHandler

import settings
import canvas_objects

app = Flask(__name__)
app.secret_key = settings.secret_key
app.config.from_object(settings.configClass)


# ============================================
# Logging
# ============================================

formatter = logging.Formatter(settings.LOG_FORMAT)
handler = RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=settings.LOG_MAX_BYTES,
    backupCount=settings.LOG_BACKUP_COUNT
)
handler.setLevel(logging.getLevelName(settings.LOG_LEVEL))
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# ============================================
# Utility Functions
# ============================================

def return_error(msg):
    return render_template('error.htm.j2', msg=msg)


def error(exception=None):
    app.logger.error("PyLTI error: {}".format(exception))
    return return_error('''Authentication error,
        please refresh and try again. If this error persists,
        please contact support.''')


# ============================================
# Web Views / Routes
# ============================================

# LTI Launch
@app.route('/launch', methods=['POST', 'GET'])
@lti(error=error, request='initial', role='any', app=app)
def launch(lti=lti):
    """
    Returns the launch page
    request.form will contain all the lti params
    """

    # example of getting lti data from the request
    # let's just store it in our session
    # variables can be found here:
    # https://github.com/instructure/canvas-lms/blob/stable/gems/lti_outbound/lib/lti_outbound/tool_launch.rb
    session['lis_person_name_full'] = request.form.get('lis_person_name_full')
    session['custom_canvas_user_id'] = request.form.get('custom_canvas_user_id')

    session['custom_canvas_course_id'] = request.form.get(
        'custom_canvas_course_id')
    session['context_title'] = request.form.get(
        'context_title')

    # username = session['lis_person_name_full']
    coursename = session['context_title']
    cid = session['custom_canvas_course_id']

    this_course = canvas_objects.Course(name=coursename, cid=cid)
    these_modules = this_course.get_modules()

    return render_template(
        'modules_list.htm.j2',
        course_obj=this_course,
        module_list=these_modules)
'''
    # Write the lti params to the console
    app.logger.info(json.dumps(request.form, indent=2))

    return render_template(
        'launch.htm.j2',
        username=username,
        coursename=coursename
    )
'''


@app.route("/selected_items/", methods=['POST'])
def selected_items():
    #  This should return a list of the urls of all the checked boxes
    # body html uses unicode

    form_data = [
        canvas_objects.CourseItem.from_url(
            url
        ) for url in request.form.getlist('module_items')
    ]

    static = 'static/'
    download_location = 'downloads/' + \
        session['custom_canvas_user_id'] + \
        session['context_title'] + 'course-archive.zip'
    download_to = static + download_location

    with ZipFile(download_to, 'w') as z_file:
        for obj in form_data:
            z_file.writestr(
                obj.file_path,
                obj.item_content()
            )

    return render_template(
        'download_page.htm.j2',
        data=form_data,
        item_count=len(form_data),
        download_location=download_location
    )


# Home page
@app.route('/', methods=['GET'])
def index(lti=lti):
    return render_template('index.htm.j2')


# LTI XML Configuration
@app.route("/xml/", methods=['GET'])
def xml():
    """
    Returns the lti.xml file for the app.
    XML can be built at https://www.eduappcenter.com/
    """
    try:
        return Response(render_template(
            'lti.xml.j2'), mimetype='application/xml'
        )
    except:
        app.logger.error("Error with XML.")
        return return_error('''Error with XML. Please refresh and try again. If this error persists,
            please contact support.''')
