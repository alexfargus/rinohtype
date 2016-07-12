# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.attribute import OptionSet, Bool
from rinoh.dimension import CM
from rinoh.document import DocumentPart
from rinoh.structure import TableOfContentsSection
from rinoh.template import (DocumentTemplate, PageTemplate, TitlePageTemplate,
                            ContentsPartTemplate, FixedDocumentPartTemplate,
                            TemplateConfiguration, TemplateOption,
                            DocumentPartTemplate)


__all__ = ['Article', 'TITLE', 'FRONT_MATTER']


TITLE = 'title'
FRONT_MATTER = 'front_matter'


class AbstractLocation(OptionSet):
    values = TITLE, FRONT_MATTER


class ArticleFrontMatter(DocumentPartTemplate):
    def document_part(self, document_section):
        document = document_section.document
        meta = document.metadata
        abstract_loc = document.configuration.get_option('abstract_location')
        flowables = []
        if 'abstract' in meta and abstract_loc == FRONT_MATTER:
            flowables.append(meta['abstract'])
        if document.configuration.get_option('table_of_contents'):
            flowables.append(TableOfContentsSection())
        if flowables:
            return DocumentPart(document_section,
                                self.page_template, self.left_page_template,
                                flowables)


class Article(DocumentTemplate):

    class Configuration(TemplateConfiguration):
        table_of_contents = TemplateOption(Bool, True,
                                           'Show or hide the table of contents')
        abstract_location = TemplateOption(AbstractLocation, FRONT_MATTER,
                                           'Where to place the abstract')

        title_page = TitlePageTemplate(top_margin=8*CM)
        page = PageTemplate(chapter_title_flowables=None)

    parts = [FixedDocumentPartTemplate([], Configuration.title_page),
             ArticleFrontMatter(Configuration.page),
             ContentsPartTemplate(Configuration.page)]
