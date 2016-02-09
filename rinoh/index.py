# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .annotation import NamedDestination, AnnotatedText
from .flowable import GroupedFlowables, GroupedFlowablesStyle, DummyFlowable
from .paragraph import Paragraph
from .reference import Referenceable, Reference, PAGE
from .style import Styled
from .text import SingleStyledText, MixedStyledText, StyledText
from .util import intersperse


__all__ = ['Index', 'IndexStyle', 'IndexTerm',
           'TextWithIndexTarget', 'InlineIndexTarget', 'IndexTarget']


class IndexStyle(GroupedFlowablesStyle):
    pass


class Index(GroupedFlowables):
    style_class = IndexStyle
    location = 'index'

    def __init__(self, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.source = self

    def flowables(self, container):
        document = container.document
        def page_refs(index_terms):
            return intersperse((Reference(target.get_id(document), PAGE)
                                for term, target in index_terms), ', ')

        index_entries = container.document.index_entries
        entries = sorted(index_entries, key=lambda s: s.lower())
        for entry in entries:
            subentries = index_entries[entry]
            try:
                top_refs = subentries[None]
                page_refs_list = ', ' + MixedStyledText(page_refs(top_refs))
            except KeyError:
                page_refs_list = None
            yield Paragraph(SingleStyledText(entry) + page_refs_list,
                            style='index entry')
            for subentry in sorted((name for name in subentries if name),
                                   key=lambda s: s.lower()):
                links = subentries[subentry]
                page_refs_list = ', ' + MixedStyledText(page_refs(links))
                yield Paragraph(SingleStyledText(subentry) + page_refs_list,
                                style='index subentry')


class IndexTerm(object):
    def __init__(self, target, name, subentry_name=None):
        self.name = name
        self.subentry_name = subentry_name
        self.target = target

    @property
    def name_tuple(self):
        return self.name, self.subentry_name

    def __eq__(self, other):
        return self.name_tuple == other.name_tuple

    def __lt__(self, other):
        return self.name_tuple < other.name_tuple

    def __hash__(self):
        return hash(self.name_tuple)


class IndexTargetBase(Styled):
    def __init__(self, index_terms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_terms = index_terms

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        index_entries = flowable_target.document.index_entries
        for index_term in self.index_terms:
            pair = index_term, self
            entries = index_entries.setdefault(index_term.name, {})
            subentries = entries.setdefault(index_term.subentry_name, [])
            subentries.append(pair)


class InlineIndexTargetBase(IndexTargetBase):
    def __init__(self, index_terms, id, *args, **kwargs):
        super().__init__(index_terms, *args, **kwargs)
        self._id = id

    def get_id(self, document):
        return self._id


class TextWithIndexTarget(InlineIndexTargetBase, AnnotatedText):
    def __init__(self, index_terms, text_or_items, id, style=None, parent=None):
        super().__init__(index_terms, text_or_items, NamedDestination(str(id)),
                         style=style, parent=parent)

    def spans(self, container):
        document, page = container.document, container.page
        document.page_references[self.get_id(document)] = page.number
        return super().spans(container)


class InlineIndexTarget(InlineIndexTargetBase, StyledText):
    def __init__(self, index_terms, id, style=None, parent=None):
        super().__init__(index_terms, id, style=style, parent=parent)

    def spans(self, container):
        container.canvas.annotate(NamedDestination(str(self._id)), 0,
                                  container.cursor, container.width, None)
        document, page = container.document, container.page
        document.page_references[self._id] = page.number
        return iter([])


class IndexTarget(IndexTargetBase, DummyFlowable, Referenceable):
    category = 'Index'

    def __init__(self, index_terms, parent=None):
        super().__init__(index_terms, parent=parent)

    def flow(self, container, last_descender, state=None):
        self.create_destination(container, container.cursor)
        self.update_page_reference(container.page)
        return super().flow(container, last_descender, state=state)