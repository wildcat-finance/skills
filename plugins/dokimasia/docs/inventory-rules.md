# Inventory rules, version 1

What `dokimasia inventory` recognises in a Next.js App Router checkout, and
what it does not. The rules identifier is `dokimasia-inventory-rules/v1` and it
is recorded in every inventory, so a record made under different rules cannot
be mistaken for one made under these.

The inventory is a denominator. It says what the application declares, so that
reviewed rows can be placed against it and the remainder named. It says nothing
about whether any item works.

## What is read

Files ending `.ts`, `.tsx`, `.js`, `.jsx` or `.mjs`, under one declared root.
Nothing else is opened. `node_modules`, `.next`, `.git`, build output,
`storybook-static` and similar generated directories are skipped, and any
directory holding a `.git` entry is pruned as a separate checkout, so a nested
worktree does not get inventoried twice.

Every read is bounded. A file over 1,048,576 bytes refuses, a tree deeper than
32 levels refuses, and a tree holding more than 20,000 source files refuses.
Symlinks are never followed, absolute paths and parent-directory segments
refuse, and no path may resolve outside the declared root. The caps are
recorded in the inventory beside the items they bounded.

## What each kind means

| Kind | Recognised from |
| --- | --- |
| `route` | a `page` file under an `app` directory |
| `api` | a `route` file under an `app` directory, with its exported HTTP methods |
| `action` | a module whose directive prologue holds `use server`, with its exported names |
| `guard` | a `middleware` file at the top of the tree, with its matchers; or a module exporting a declared gate name |

A URL comes from the directory path between the `app` directory and the file.
Segments in parentheses are route groups and contribute nothing. Segments
beginning `@` are parallel routes and contribute nothing. Dynamic, catch-all and
optional catch-all segments keep their bracket form, because the inventory
records the shape the source declares rather than one filled-in example.

Recognition runs over a scanner, not over raw bytes. Comments, string bodies,
template literals and regular-expression bodies cannot produce an item, so a
commented `export const GET` and a quoted `"use server"` are both absent from
the inventory. The committed fixture holds one of each as a decoy and a test
requires their absence.

## The digest

The inventory digest covers the schema, the rules identifier, the caps and the
items. It does not cover the subject label or the root path, so two compiles of
the same tree agree on any machine. Items are sorted, no clock is read, and no
environment value reaches the digested bytes.

## What these rules do not establish

They do not establish that the rule set is complete for Next.js, or for any
other framework. A convention these rules do not name produces no item, and the
inventory cannot distinguish that from an application that does not use it.

Client-side gates are found by exported name against a declared list. A gate the
list does not name is absent from the inventory; that is a gap in the list, not
a finding about the application.

Export clauses are not alias-resolved. `export { DELETE as REMOVE }` records
both names, so a handler is not missed, at the cost of recording a name the
module does not answer on.

An item's presence says the source declares it. It does not say the item is
reachable at runtime, that a route renders, that a handler responds, or that
anything has been tested. Reachability, behaviour and coverage are other
questions, and the later steps of the runbook own them.

## Changing these rules

A change to what counts as an item changes every recorded inventory digest and
therefore every disposition recorded against one. Bump the rules identifier,
state what moved, and say what happens to records made under the previous
version.
