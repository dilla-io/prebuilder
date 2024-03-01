# Prebuilder

## Setup

```shell
make build
```

Environment variables:

- `SCHEMA`: URL of generic JSON schema. Default value: [https://gitlab.com/dilla-io/schemas/-/raw/master/renderable.schema.json](https://gitlab.com/dilla-io/schemas/-/raw/master/renderable.schema.json)

## Usage

```shell
docker login registry.gitlab.com
docker pull registry.gitlab.com/dilla-io/prebuilder
```

```shell
docker run -u $(id -u):$(id -g) \
   -v $YOUR_PATH:/data/input -v $OTHER_PATH:/data/output:rw \
   -t registry.gitlab.com/dilla-io/prebuilder run [cdn]
```

Where:

- `cdn`: the destination of the static data. Default value: https://data.dilla.io/{system_id}/

The prebuilder will look for every design systems inside the first mounted volume, and will generate in the same position inside the second mounted volume:

- a `build/` folder with the prebuild
- a `data/` folder with extracted static assets

## Result

For each design system, inside the `build/` folder:

- {design_system_id}.rs : Rust structs about the design system, used for rendering
- {design_system_id}.json : All the definitions about the design system, used for introspection
- renderable.schema.json : A specific JSON schema for renderable payload, used by the dev tools
- components/{component_id}/{component_id}.jinja
- components/{component_id}/{component_id}-{variant_id}.jinja
- components/{component_id}/{example_id}.json : Test data
