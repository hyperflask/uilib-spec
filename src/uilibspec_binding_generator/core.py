import os
import yaml


class UIComponent:
    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            source = f.read()
        return cls.from_source(os.path.splitext(os.path.basename(filename))[0], source)
    
    @classmethod
    def from_source(cls, name, source):
        source, frontmatter = extract_frontmatter(source)
        return cls(name, source, **cls.process_frontmatter(frontmatter))
    
    @classmethod
    def process_frontmatter(cls, frontmatter):
        if not frontmatter:
            return {}
        kwargs = {}
        if "innerHTML" in frontmatter:
            kwargs.setdefault("props", {})["innerHTML"] = frontmatter["innerHTML"]
        if "props" in frontmatter:
            kwargs["props"] = Property.from_config(frontmatter["props"])
        if "children" in frontmatter:
            kwargs["children"] = Transformation.from_dict(frontmatter["children"], fence=Fence(ChildrenSlot))
            kwargs["children"].innerHTML = ChildrenSlot
        return kwargs

    def __init__(self, name, template, props=None, children=None):
        self.name = name
        self.template = template
        self.props = props or {}
        self.children = children

    def __repr__(self):
        return f"<{self.name}>{repr(self.props)}<children>{repr(self.children)}</children></{self.name}>"


class Property:
    @classmethod
    def from_config(cls, config):
        props = {}
        if isinstance(config, dict):
            config = [{k: v} for k, v in config.items()]
        for spec in config:
            name, spec = spec.popitem()
            spec = dict(spec)
            missings = []
            required = False
            default = None

            if isinstance(spec, dict):
                if "missing" in spec:
                    if isinstance(spec["missing"], list):
                        missings.extend(spec.pop("missing"))
                    else:
                        missings.append(spec.pop("missing"))
                required = spec.pop("required", False)
                default = spec.pop("default", None)
                if not "transformations" in spec:
                    spec = {"transformations": [spec]}
            else:
                spec = {"transformations": spec}

            transfos = []
            for entry in spec["transformations"]:
                if "slot" in entry and not missings:
                    required = True
                tf = Transformation.front_config(name, entry, True if "slot" in entry else required)
                transfos.append(tf)

            if missings:
                for missing in missings:
                    missing = dict(missing)
                    if not missing.get("target") and "slot" not in missing:
                        missing["target"] = transfos[0].target
                    missing["match"] = {"$undefined": True}
                    transfos.append(Transformation.front_config(name, missing))

            props[name] = cls(name, transfos, bool(required), default)
        return props
    
    def __init__(self, name, transformations, required=False, default=None):
        self.name = name
        self.transformations = transformations
        self.required = required
        self.default = default

    def __repr__(self):
        return f"<{self.name} required={self.required} default={repr(self.default)}>{repr(self.transformations)}</>"


class Transformation:
    @classmethod
    def front_config(cls, prop, config, required=False):
        if "slot" in config:
            target = 'slot[name="%s"]' % config["slot"]
            outerHTML = config.get("outerHTML", "{}")
            innerHTML = None
        else:
            target = config.get("target", "&")
            innerHTML = config.get("innerHTML")
            outerHTML = config.get("outerHTML")

        match = None
        if "match" in config:
            match = Condition.from_config(prop, config["match"])
        elif not required:
            match = Condition(prop, "$undefined", False)

        attrs = config.get("attributes", {})
        if "attribute" in config:
            attrs[config["attribute"]] = {"replace": "{}"}
        for attr in ('class', 'style'):
            if config.get(attr):
                attrs[attr] = config[attr]

        return cls(target,
                   ValueTransformation.from_attrs(attrs, prop),
                   ValueTransformation.from_value(innerHTML, prop, "replace") if innerHTML is not None else None,
                   ValueTransformation.from_value(outerHTML, prop, "replace") if outerHTML is not None else None,
                   match)
                   
    def __init__(self, target, attributes=None, innerHTML=None, outerHTML=None, match=None):
        self.target = target
        self.attributes = attributes or {}
        self.innerHTML = innerHTML
        self.outerHTML = outerHTML
        self.match = match

    def __repr__(self):
        return f"<Transformation {self.target} (attrs={repr(self.attributes)} innerHTML={repr(self.innerHTML)} outerHTML={repr(self.outerHTML)} match={repr(self.match)})>"


class ValueTransformation:
    APPEND = "append"
    PREPEND = "prepend"
    REPLACE = "replace"

    @classmethod
    def from_value(cls, value, default_prop=None, default_action="append"):
        action = default_action
        if isinstance(value, dict):
            action, value = value.popitem()
        if isinstance(value, str):
            value = value.replace("{}", "{%s}" % default_prop)
        return cls(value, action)

    @classmethod
    def from_attrs(cls, dct, default_prop=None):
        attrs = {}
        for name, value in dct.items():
            attrs[name] = cls.from_value(value, default_prop)
        return attrs

    def __init__(self, value, action="append"):
        self.value = value
        self.action = action

    def __repr__(self):
        return f"{self.action}({self.value})"


class Condition:
    @classmethod
    def from_config(cls, prop, config):
        if isinstance(config, dict):
            op, value = config.popitem()
        else:
            op = "$eq"
            value = config
        return cls(prop, op, value)

    def __init__(self, property, op, value):
        self.property = property
        self.op = op
        self.value = value

    def __repr__(self):
        return f"<{self.property} {self.op} {self.value}>"


class _ChildrenSlot:
    def __repr__(self):
        return "<Children>"

ChildrenSlot = _ChildrenSlot()


def extract_frontmatter(source):
    if source.startswith("---\n"):
        frontmatter_end = source.find("\n---\n", 4)
        if frontmatter_end == -1:
            frontmatter = source[4:]
            source = ""
        else:
            frontmatter = source[4:frontmatter_end]
            source = source[frontmatter_end + 5:]
        return source, yaml.safe_load(frontmatter)
    return source, None