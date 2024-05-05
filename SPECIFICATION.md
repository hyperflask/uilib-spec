# UILibSpec Specifications

This is a first draft.

## Glossary

- **Component**
- **Property**
- **Transformation**
- **Frontmatter**

## Component structure

A component file contains a YAML frontmatter and an HTML template.

- files sould have the *html* extension
- component name is its filename without the extension
- has a list of properties
- each property is mapped to a set of transformations
- these transformations are applied if the property is defined
- the transformations mutate the HTML template
- [slots](https://developer.mozilla.org/fr/docs/Web/HTML/Element/slot) can be used as placeholders in the html template

## Frontmatter schema

### Component schema

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| props | [`Array[Hash[String, Property]]`](#property-schema) | No | |
| children | [`Transformation`](#transformation-schema) | No | |
| help | `String` | No | |

### Property schema

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| transformations | [`Array[Transformation]`](#transformation-schema) | Yes | |
| required | `Bool` | No | |
| default | `Any` | No | |
| missing | [`Array[Transformation]`](#transformation-schema) | No | |
| help | `String` | | |

### Transformation schema

| Property | Type | Required  | Description |
| --- | --- | --- | --- |
| target | `String` | Yes | |
| attributes | [`Hash[String, ValueTransformation]`](#valuetransformation-schema) | No | |
| innerHTML | [`ValueTransformation`](#valuetransformation-schema) | No | |
| outerHTML | [`ValueTransformation`](#valuetransformation-schema) | No | |
| match | [`Array[Condition]`](#condition-schema) | No | |

### ValueTransformation schema

A hash one entry where the key the action and the value the value.

Possible actions: replace, append, prepend

```
{"replace": "hello world"}
```

Curly brackets with the name a prop `{name}` can be used as placeholder for the property value. `{}` is a shorthand for the property the transformation belongs to.

### Condition schema

A hash with one entry where the key is the operator and the value the value.

Possible operators: $eq, $neq, $undefined

```
{"$eq": true}
```

### Slots

`<slot></slot>` can be used to define placeholders.

For slots which are not referenced in any transformation target:

 - named slots are automatically mapped to a same name property
 - a single unnamed slot is automatically mapped to the children