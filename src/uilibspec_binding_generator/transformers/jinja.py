from ..transformer import Transformer, html_attrs, html_attr
from ..core import ChildrenSlot
import re


class JinjaTransfomer(Transformer):
    def before_template(self, component, props):
        reqs = []
        optional = []
        for name, required, default in props:
            name = name.replace("-", "_")
            if required:
                reqs.append(name)
            else:
                optional.append("%s=%s" % (name, "None"))
        self.indent_level += 1
        return "{%% macro %s(%s) -%%}" % (component.name, ", ".join(reqs + optional))
    
    def after_template(self, component, props):
        return "{%- endmacro %}"
    
    def walk_open_tag(self, tag_name, attrs, transformations):
        fence = []
        innerHTML = ""
        skip_children = False

        fence = ""
        for tf in transformations:
            if tf.outerHTML:
                if tf.outerHTML.action == "replace":
                    fence = self.fence(tf, self.interpolate(tf.outerHTML.value), close=False)
                    if not tf.match:
                        return fence, True
                elif tf.outerHTML.action == "prepend":
                    fence = self.fence(tf, self.interpolate(tf.outerHTML.value) + " ") + fence
            if tf.innerHTML:
                if tf.innerHTML.action == "replace":
                    innerHTML += self.fence(tf, self.interpolate(tf.innerHTML.value), close=False)
                    skip_children = not bool(tf.match)
                elif tf.innerHTML.action == "prepend":
                    innerHTML = self.fence(tf, self.interpolate(tf.innerHTML.value) + " ") + innerHTML
            for k, v in tf.attributes.items():
                if v.action == "replace" or k not in attrs:
                    if k not in attrs:
                        a = self.fence(tf, html_attr(k, self.interpolate(v.value)))
                        attrs[k] = lambda k: a
                    else:
                        attrs[k] = self.fence(tf, self.interpolate(v.value), False) + attrs[k] + "{% endif %}"
                elif v.action == "append":
                    attrs[k] = attrs.get(k, "") + self.fence(tf, " " + self.interpolate(v.value))
                elif v.action == "prepend":
                    attrs[k] = self.fence(tf, self.interpolate(v.value) + " ") + attrs.get(k, "")

        return "%s<%s %s>%s" % (fence, tag_name, html_attrs(attrs), innerHTML), skip_children
    
    def walk_close_tag(self, tag_name, attrs, transformations):
        after = ""
        before = ""
        for tf in transformations:
            if tf.outerHTML and tf.outerHTML.action == "replace":
                if not tf.match:
                    return ""
                after += "{% endif %}"
            if tf.innerHTML and tf.innerHTML.action == "replace" and tf.match:
                before += "{% endif %}"
        return "%s</%s>%s" % (before, tag_name, after)
    
    def fence(self, transformation, value, close=True):
        if value is ChildrenSlot:
            value = "caller"
        if not transformation.match:
            return value
        return "{%% if %s %%}%s%s" % (self.walk_condition(transformation.match), value, "{% endif %}" if close else "{% else %}")
    
    def walk_condition(self, condition):
        prop = condition.property.replace("-", "_")
        if condition.op == "$eq":
            return f"{prop} == '{condition.value}'"
        if condition.op == "$neq":
            return f"{prop} != '{condition.value}'"
        if condition.op == "$undefined":
            return f"not {prop}" if condition.value else prop
        return prop
    
    def interpolate(self, value):
        if value is ChildrenSlot:
            return "{{ caller() }}"
        for m in re.findall("\{([^}]+)\}", value):
            value = value.replace(m, "{%s}" % m.replace("-", "_"))
        return value