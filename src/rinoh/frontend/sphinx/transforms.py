from typing import Any, Dict, List, Set, Tuple, cast

from docutils import nodes
from docutils.nodes import Element, Node, Text
from docutils.transforms.references import Substitutions

from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.builders.latex.nodes import (captioned_literal_block, footnotemark, footnotetext,
                                         math_reference, thebibliography)
from sphinx.domains.citation import CitationDomain
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.nodes import NodeMatcher


class RinohCitationReferenceTransform(SphinxPostTransform):
    default_priority = 5  # before ReferencesResolver
    formats = ('pdf',)
    builders = ('rinoh',)


    def run(self, **kwargs) -> None:
        domain = cast(CitationDomain, self.env.get_domain('citation'))
        matcher = NodeMatcher(addnodes.pending_xref, refdomain='citation', reftype='ref')
        for node in self.document.traverse(matcher):  # type: addnodes.pending_xref
            docname, labelid, _ = domain.citations.get(node['reftarget'], ('', '', 0))

            if docname:
                child = Text(node['reftarget'])
                citation_ref = nodes.citation_reference('', '', child,
                                                        docname=docname, refid=labelid)
                node.replace_self(citation_ref)
