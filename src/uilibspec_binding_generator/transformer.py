from bs4 import BeautifulSoup, NavigableString
from .core import Transformation, ValueTransformation, ChildrenSlot


class Transformer:
    def transform(self, component):
        soup = BeautifulSoup(component.template, "html.parser", multi_valued_attributes=None)
        transformations = []
        tags_transfo_map = {}
        props = []

        for prop in component.props.values():
            props.append((prop.name, prop.required, prop.default))
            transformations.extend(prop.transformations)

        if not component.children:
            transformations.append(Transformation("slot:not([name])", outerHTML=ValueTransformation(ChildrenSlot, "replace")))
        else:
            transformations.append(component.children)

        for tf in transformations:
            if tf.target == "&":
                tag = soup.contents[0]
            else:
                tag = soup.select_one(tf.target)
            if tag:
                tags_transfo_map.setdefault(tag, []).append(tf)

        for slot in soup.select("slot"):
            if slot not in tags_transfo_map:
                tags_transfo_map[slot] = [Transformation('slot[name"%s"]' % slot.name, outerHTML=ValueTransformation("{%s}" % slot.name, "replace"))]
                props.append((slot.name, True, None))

        self.indent_level = 0
        out = self.walk(soup, component, props, tags_transfo_map)
        return "\n".join(filter(None, out))
    
    def walk(self, soup, component, props, transformations):
        yield self.before_template(component, props)
        yield from self.walk_tag(soup.contents[0], transformations)
        yield self.after_template(component, props)
    
    def before_template(self, component, props):
        raise NotImplementedError()
    
    def after_template(self, component, props):
        raise NotImplementedError()

    def walk_tag(self, tag, transformations):
        if isinstance(tag, NavigableString):
            return self.indent(self.walk_string(tag))
        attrs = dict(tag.attrs)
        tag_transformations = transformations.get(tag, [])
        out, skip_children = self.walk_open_tag(tag.name, attrs, tag_transformations)
        yield self.indent(out)
        if not skip_children:
            self.indent_level += 1
            for child in tag.contents:
                yield from self.walk_tag(child, transformations)
            self.indent_level -= 1
        yield self.indent(self.walk_close_tag(tag.name, attrs, tag_transformations))
    
    def walk_string(self, string):
        return string.strip()

    def walk_open_tag(self, tag_name, attrs, transformations):
        raise NotImplementedError()
    
    def walk_close_tag(self, tag_name, attrs, transformations):
        return "</%s>" % tag_name
    
    def indent(self, text):
        return " " * self.indent_level * 4 + text


def html_attrs(attrs=None, **kwargs):
    attrs = dict(attrs or {})
    attrs.update(kwargs)
    html = []
    for k, v in attrs.items():
        if v is None:
            continue
        if callable(v):
            html.append(v(k))
        else:
            html.append(html_attr(k, v))
    return " ".join(html)


def html_attr(name, value):
    if name.endswith('_'):
        name = name[:-1]
    name = name.replace("_", "-")
    if isinstance(value, bool):
        return name
    return '%s="%s"' % (name, str(value).strip())