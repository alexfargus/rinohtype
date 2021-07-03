from typing import cast
from os import path

from docutils import nodes
from docutils.nodes import Text
from sphinx import addnodes
from sphinx.domains.citation import CitationDomain
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.nodes import NodeMatcher

from sphinxcontrib.plantuml import PlantumlBuilder, render_plantuml, plantuml

class RinohCitationReferenceTransform(SphinxPostTransform):
    default_priority = 5  # before ReferencesResolver
    formats = ('pdf',)
    builders = ('rinoh',)

    def run(self, **kwargs) -> None:
        domain = cast(CitationDomain, self.env.get_domain('citation'))
        pending_xref = NodeMatcher(addnodes.pending_xref, refdomain='citation',
                                    reftype='ref')
        for node in self.document.traverse(pending_xref):
            doc, refid, _ = domain.citations.get(node['reftarget'], ('', '', 0))
            if doc:
                child = Text(node['reftarget'])
                citation_ref = nodes.citation_reference('', '', child,
                                                        docname=doc,
                                                        refid=refid)
                node.replace_self(citation_ref)


class RinohPlantumlTransform(SphinxPostTransform):
    default_priority = 10
    formats = ('pdf',)
    builders = ('rinoh',)

    def run(self, **kwargs) -> None:
        rinoh_builder = self.env.app.builder
        plantuml_builder = rinoh_builder.plantuml_builder
        for node in self.document.traverse(plantuml):
            try:
                image_name, image_path = render_plantuml(self.env.app, node, 'png')
            except PlantUmlError as err:
                logger.warning(str(err))
                raise nodes.SkipNode
            kwargs = {attr: node.get(attr) for attr in ('scale', 'width', 'height') if attr in node}
            image_node = nodes.image(uri=image_path, alt=node.get('alt', node['uml']), **kwargs)
            image_node['candidates']= {'*': path.join(self.app.srcdir, image_path)}
            node.parent.replace(node, image_node)
            self.env.images.add_file(self.env.docname, image_path)
