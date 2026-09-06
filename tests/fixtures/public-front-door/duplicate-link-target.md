<!-- front-door-specimen: expect="FD07" reason="one link target appears twice" -->
<p align="center">
  <img src="./assets/characters/shoggoth.png" width="1200" alt="The Shoggoth collective">
</p>

# THE SPECIMEN COLLECTIVE

A synthetic front door for a synthetic tree. It holds
<!-- front-door:count key="governed" -->{{count:governed}} governed skills in
<!-- front-door:count key="plugins" -->{{count:plugins}} plugins. No id here is
one this repository uses.

## SO, YOU WANT TO BUILD GOD?

Ask the Atlas for a number. Pick your harness. Finish what you start.

Start at [how to help](./docs/how-to-help-shoggoth.md), which offers a small
route as well as the controlled one.

<!-- front-door:aside -->
Written by the thing it describes. Read the evidence, not the prose.

## WHAT CAN IT DO?

The members below rebuild something held, offline, from preserved bytes.

### LANTERN REBUILDS ITS HELD SPECIMEN

<!-- front-door:demo skill="lantern" claim="{{claim:lantern}}" digest="{{digest:lantern}}" -->
[Lantern](./plugins/lantern) rebuilds the specimen it preserved.

Run `python3 scripts/demonstrations.py run --record {{directory:lantern}} --report tmp/demo/lantern.json`
over the preserved `{{source:lantern}}` and it reports `{{observed:lantern}}`.
{{nonclaim:lantern}}

### THICKET REBUILDS ITS HELD SPECIMEN

<!-- front-door:demo skill="thicket" claim="{{claim:thicket}}" digest="{{digest:thicket}}" -->
[Thicket](./plugins/thicket) rebuilds the specimen it preserved.

Run `python3 scripts/demonstrations.py run --record {{directory:thicket}} --report tmp/demo/thicket.json`
over the preserved `{{source:thicket}}` and it reports `{{observed:thicket}}`.
{{nonclaim:thicket}}

## WHAT A RESULT MEANS

The [Promise Machine contract](./PROMISE_MACHINE.md) is the shared law between
these members. It does not certify that a domain claim is true.

## THE REST OF THE COLLECTIVE

[The catalogue](./FUTUREPROOFING.md) lists every member, including the
<!-- front-door:count key="domain" -->{{count:domain}} domain agents this tree
derives, and [the catalogue again](./FUTUREPROOFING.md) is the same page.
