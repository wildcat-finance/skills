// Dev-time oracle for the Horos TypeScript outliner. Never imported or
// executed by the shipped plugin or its test suite: the differential corpus
// run drives it by hand, with the `typescript` package installed outside
// the repository, and only the recorded results are committed.
//
// Usage: node ts_oracle.mjs <file.ts> [...] > oracle.json
//
// Emits, per file, the declarations the compiler sees at the altitudes the
// outliner claims: module level, module/namespace blocks, and class
// members. Function-body locals are deliberately absent on both sides.

import ts from "typescript";
import { readFileSync } from "node:fs";

const out = {};

for (const file of process.argv.slice(2)) {
  const text = readFileSync(file, "utf8");
  const kind = file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind);
  const decls = [];
  const lineOf = (node) =>
    sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
  const push = (name, node, kind) => {
    if (name) decls.push({ name, line: lineOf(node), kind });
  };

  const visitMembers = (cls) => {
    for (const m of cls.members) {
      if (ts.isConstructorDeclaration(m)) push("constructor", m, "member");
      else if (m.name && ts.isIdentifier(m.name)) push(m.name.text, m, "member");
    }
  };

  const visitStatements = (statements) => {
    for (const st of statements) {
      if (ts.isFunctionDeclaration(st)) push(st.name?.text, st, "function");
      else if (ts.isClassDeclaration(st)) {
        push(st.name?.text, st, "class");
        visitMembers(st);
      } else if (ts.isInterfaceDeclaration(st)) push(st.name.text, st, "interface");
      else if (ts.isTypeAliasDeclaration(st)) push(st.name.text, st, "type");
      else if (ts.isEnumDeclaration(st)) push(st.name.text, st, "enum");
      else if (ts.isModuleDeclaration(st)) {
        push(
          ts.isIdentifier(st.name) || ts.isStringLiteral(st.name)
            ? st.name.text
            : st.name.getText(sf),
          st,
          "namespace"
        );
        if (st.body && ts.isModuleBlock(st.body)) visitStatements(st.body.statements);
      } else if (ts.isVariableStatement(st)) {
        for (const d of st.declarationList.declarations) {
          if (ts.isIdentifier(d.name)) push(d.name.text, d, "variable");
        }
      }
    }
  };

  visitStatements(sf.statements);
  out[file] = decls;
}

process.stdout.write(JSON.stringify(out));
