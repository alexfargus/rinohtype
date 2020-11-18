# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections import namedtuple

import pytest

from docutils.utils import new_document
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace

from rinoh.document import DocumentTree
from rinoh.frontend.sphinx import (template_from_config, set_document_metadata,
                                   deprecation_warnings)
from rinoh.language import IT
from rinoh.paper import A4, LETTER
from rinoh.templates import Book, Article


def create_sphinx_app(tmpdir, **confoverrides):
    app = Sphinx(srcdir=tmpdir.strpath,
                 confdir=None,
                 outdir=(tmpdir / 'output').strpath,
                 doctreedir=(tmpdir / 'doctrees').strpath,
                 buildername='rinoh',
                 confoverrides=confoverrides)
    return app


def create_document(title='A Title', author='Ann Other', docname='a_name'):
    document = new_document('/path/to/document.rst')
    document.settings.title = title
    document.settings.author = author
    document.settings.docname = docname
    return document


def create_logger():
    MockLogger = namedtuple('MockLogger', ['warning', 'warnings'])
    warnings = []
    def capture_warning(msg):
        warnings.append(msg)
    return MockLogger(capture_warning, warnings)


CONFIG_DIR = 'confdir'


def get_contents_page_size(template_configuration):
    doctree = DocumentTree([])
    doc = template_configuration.document(doctree)
    part_template = doc.part_templates[2]
    part = part_template.document_part(doc)
    assert part.template_name == 'contents'
    page = part.new_page(1, new_chapter=False)
    return page.get_config_value('page_size', doc)


def get_template_cfg(tmpdir, **confoverrides):
    with docutils_namespace():
        app = create_sphinx_app(tmpdir, **confoverrides)
        template_cfg = template_from_config(app.config, CONFIG_DIR, print)
    return template_cfg


def test_sphinx_config_default(tmpdir):
    template_cfg = get_template_cfg(tmpdir)
    assert template_cfg.template == Book
    assert not template_cfg.keys()
    assert template_cfg.variables.keys() == set(['paper_size'])
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_latex_elements_papersize(tmpdir):
    template_cfg = get_template_cfg(
        tmpdir, latex_elements=dict(papersize='a4paper'))
    assert template_cfg.template == Book
    assert not template_cfg.keys()
    assert template_cfg.variables.keys() == set(['paper_size'])
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_rinoh_paper_size(tmpdir):
    template_cfg = get_template_cfg(tmpdir, rinoh_paper_size=A4,
                                    latex_elements=dict(papersize='a4paper'))
    assert template_cfg.template == Book
    assert not template_cfg.keys()
    assert template_cfg.variables.keys() == set(['paper_size'])
    assert get_contents_page_size(template_cfg) == A4


def test_sphinx_config_language(tmpdir):
    template_cfg = get_template_cfg(tmpdir, language='it')
    assert template_cfg.template == Book
    assert template_cfg['language'] == IT


def test_sphinx_config_rinoh_template(tmpdir):
    template_cfg = Article.Configuration('test',
                                         stylesheet='sphinx_article')
    template_cfg = get_template_cfg(tmpdir, rinoh_template=template_cfg)
    assert template_cfg.template == Article
    assert (template_cfg.get_attribute_value('stylesheet').name
            == 'Sphinx (article)')


def test_sphinx_config_rinoh_template_from_entrypoint(tmpdir):
    template_cfg = get_template_cfg(tmpdir, rinoh_template='book')
    assert not template_cfg.keys()
    assert template_cfg.template == Book
    assert template_cfg.get_attribute_value('stylesheet').name == 'Sphinx'


def test_sphinx_config_rinoh_template_from_filename(tmpdir):
    template_cfg_path = tmpdir.join('template_cfg.rtt').strpath
    with open(template_cfg_path, 'w') as template_cfg:
        print('[TEMPLATE_CONFIGURATION]', file=template_cfg)
        print('template = book', file=template_cfg)
    template_cfg = get_template_cfg(tmpdir, rinoh_template=template_cfg_path)
    assert not template_cfg.keys()
    assert template_cfg.template == Book
    assert template_cfg.get_attribute_value('stylesheet').name == 'Sphinx'


def test_sphinx_set_document_metadata(tmpdir):
    app = create_sphinx_app(tmpdir, release='1.0', rinoh_template='book')
    template_cfg = template_from_config(app.config, CONFIG_DIR, print)
    docutils_tree = create_document()
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    set_document_metadata(rinoh_doc, app.config, docutils_tree)
    assert rinoh_doc.metadata['title'] == 'A Title'
    assert rinoh_doc.metadata['subtitle'] == 'Release 1.0'
    assert rinoh_doc.metadata['author'] == 'Ann Other'
    assert 'date' in rinoh_doc.metadata


def test_sphinx_set_document_metadata_subtitle(tmpdir):
    expected_subtitle = 'A subtitle'
    app = create_sphinx_app(tmpdir, rinoh_metadata={
                            'subtitle': expected_subtitle})
    template_cfg = template_from_config(app.config, CONFIG_DIR, print)
    docutil_tree = create_document()
    rinoh_tree = DocumentTree([])
    rinoh_doc = template_cfg.document(rinoh_tree)
    set_document_metadata(rinoh_doc, app.config, docutil_tree)
    assert expected_subtitle == rinoh_doc.metadata['subtitle']


def test_sphinx_default_deprecation_warning(tmpdir):
    app = create_sphinx_app(tmpdir)
    logger = create_logger()
    deprecation_warnings(app.config, logger)
    assert logger.warnings == []


def test_sphinx_rinoh_stylesheet_deprecation_warning(tmpdir):
    app = create_sphinx_app(tmpdir, rinoh_stylesheet="sphinx")
    logger = create_logger()
    deprecation_warnings(app.config, logger)
    the_warning, = logger.warnings
    assert "Support for 'rinoh_stylesheet' has been removed" in the_warning


def test_sphinx_rinoh_paper_size_deprecation_warning(tmpdir):
    app = create_sphinx_app(tmpdir, rinoh_paper_size="A4")
    logger = create_logger()
    deprecation_warnings(app.config, logger)
    the_warning, = logger.warnings
    assert "Support for 'rinoh_paper_size' has been removed" in the_warning