# UILibSpec

A specification to generate component bindings for UI component libraries targeting various languages and frameworks.

 - Define your component in HTML with a YAML frontmatter detailing properties and their impact
 - Generate component bindings for various languages and frameworks (built-in: web components, react, solidjs, jinja macro)

Note: this project is in an early phase. If there is some interest towards it, then it can be developped furtger.

## Specification

See [SPECIFICATION.md](SPECIFICATION.md)

## Example

See the [examples](examples) folder.

Let's define a button using [bootstrap](https://getbootstrap.com/docs/5.3/components/buttons/)

```
---
help: A button
props:
  var:
    class: btn-{}
  type:
    attribute: type
    default: button
  outline:
    class: btn-outline-{var}
  size:
    class: btn-{}
    type:
      enum:
        - lg
        - sm
---
<button class="btn"><slot></slot></button>
```

Using the react target, this would generate the following component:

```js
function Button(props) {
  const classNames = ["btn"];
  if (props.var) {
    classNames.push(`btn-{props.var}`)
  }
  if (props.outline) {
    classNames.push(`btn-outline-{props.var}`);
  }
  if (props.size) {
    classNames.push(`btn-{props.size}`);
  }
  return (
    <button type={props.type || "button"} className={classNames.join(" ")}>{props.children}</button>
  );
}
```

## Generating bindings

The project includes a Python binding generator.

Install:

    pip install uilibspec-binding-generator

Define your components then run:

    uilibspec-binding-generator path/to/components/ path/to/output/ --target webcomponents
