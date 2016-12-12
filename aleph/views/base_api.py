import os
import six
import logging
from apikit import jsonify
from flask import render_template, current_app, Blueprint, request
from jsonschema import ValidationError
from elasticsearch import TransportError

from aleph.core import get_config, app_title, app_url, schemata
from aleph.metadata import Metadata
from aleph.schema import SchemaValidationException
from aleph.data.reference import COUNTRY_NAMES, LANGUAGE_NAMES
from aleph.views.cache import enable_cache

blueprint = Blueprint('base_api', __name__)
log = logging.getLogger(__name__)


def angular_templates():
    templates = {}
    template_dirs = [current_app.static_folder]
    template_dirs.extend(get_config('CUSTOM_TEMPLATES_DIR'))
    for template_dir in template_dirs:
        for tmpl_set in ['templates', 'help']:
            tmpl_dir = os.path.join(template_dir, tmpl_set)
            for (root, dirs, files) in os.walk(tmpl_dir):
                for file_name in files:
                    if file_name.startswith('.'):
                        continue
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'rb') as fh:
                        file_name = file_path[len(template_dir) + 1:]
                        templates[file_name] = fh.read().decode('utf-8')
    return templates.items()


@blueprint.route('/help')
@blueprint.route('/help/<path:path>')
@blueprint.route('/entities')
@blueprint.route('/entities/<path:path>')
@blueprint.route('/documents')
@blueprint.route('/documents/<path:path>')
@blueprint.route('/datasets')
@blueprint.route('/datasets/<path:path>')
@blueprint.route('/crawlers')
@blueprint.route('/crawlers/<path:path>')
@blueprint.route('/collections')
@blueprint.route('/collections/<path:path>')
@blueprint.route('/tabular/<path:path>')
@blueprint.route('/text/<path:path>')
@blueprint.route('/')
def ui(**kwargs):
    enable_cache(server_side=True)
    return render_template("layout.html", templates=angular_templates())


@blueprint.route('/api/1/metadata')
def metadata():
    enable_cache(server_side=False)
    return jsonify({
        'status': 'ok',
        'app': {
            'title': six.text_type(app_title),
            'url': six.text_type(app_url),
            'samples': get_config('SAMPLE_SEARCHES')
        },
        'fields': Metadata.facets(),
        'categories': get_config('COLLECTION_CATEGORIES', {}),
        'countries': COUNTRY_NAMES,
        'languages': LANGUAGE_NAMES,
        'schemata': schemata
    })


@blueprint.app_errorhandler(403)
def handle_authz_error(err):
    return jsonify({
        'status': 'error',
        'message': 'You are not authorized to do this.',
        'roles': request.authz.roles,
        'user': request.authz.role
    }, status=403)


@blueprint.app_errorhandler(ValidationError)
def handle_validation_error(err):
    return jsonify({
        'status': 'error',
        'message': err.message
    }, status=400)


@blueprint.app_errorhandler(SchemaValidationException)
def handle_schema_validation_error(err):
    return jsonify({
        'status': 'error',
        'errors': err.errors
    }, status=400)


@blueprint.app_errorhandler(TransportError)
def handle_es_error(err):
    log.exception(err)
    message = err.error
    for cause in err.info.get('error', {}).get('root_cause', []):
        message = cause.get('reason', message)
    return jsonify({
        'status': 'error',
        'message': message
    }, status=400)
