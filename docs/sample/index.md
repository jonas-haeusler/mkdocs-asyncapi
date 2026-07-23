# Sample

This page demonstrates embedding a [local](#local-spec) and a [remote](#remote-spec) AsyncAPI spec,
as well as [overriding the config](#inline-config-override) for a single component.

## Local spec

--8<-- "usage.md"

<div class="result" markdown>

<asyncapi-component src="streetlights.yml"/>

</div>

## Remote spec

--8<-- "remote-usage.md"

<div class="result" markdown>

<asyncapi-component src="https://raw.githubusercontent.com/asyncapi/spec/master/examples/streetlights-kafka-asyncapi.yml"/>

</div>

## Inline config override

--8<-- "config-usage.md"

<div class="result" markdown>

<asyncapi-component src="streetlights.yml" config='{"show":{"info":false}}'/>

</div>
