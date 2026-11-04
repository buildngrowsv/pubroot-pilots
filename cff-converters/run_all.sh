#!/usr/bin/env bash
# Convert every case with the three converters to BibTeX and APA-like text. Outputs: results/raw/<case>/<tool>.<fmt>
set -u; cd "$(dirname "$0")"
RB=${RUBY:-ruby}; PY=${CFFCONVERT:-py/.venv/bin/cffconvert}
mkdir -p results/raw
for f in cases/*.cff; do c=$(basename $f .cff); d=results/raw/$c; mkdir -p $d
  $RB rb/conv.rb $f validate > $d/ruby-cff.validate 2>&1
  $PY -i $f --validate > $d/cffconvert.validate 2>&1; echo "exit $?" >> $d/cffconvert.validate
  for fmt in bib apa; do
    $RB rb/conv.rb $f $fmt > $d/ruby-cff.$fmt 2>$d/ruby-cff.$fmt.err
    $PY -i $f -f $([ $fmt = bib ] && echo bibtex || echo apalike) > $d/cffconvert.$fmt 2>$d/cffconvert.$fmt.err
    node js/conv.mjs $f $fmt > $d/citation-js.$fmt 2>$d/citation-js.$fmt.err
  done
done
{ echo "ruby-cff $($RB -e 'require "cff"; puts CFF::VERSION') ruby $($RB -e 'puts RUBY_VERSION')"; echo "cffconvert $($PY --version)"; echo "citation-js core $(node -p "require('./js/node_modules/@citation-js/core/package.json').version") plugin-software-formats $(node -p "require('./js/node_modules/@citation-js/plugin-software-formats/package.json').version") plugin-bibtex $(node -p "require('./js/node_modules/@citation-js/plugin-bibtex/package.json').version") plugin-csl $(node -p "require('./js/node_modules/@citation-js/plugin-csl/package.json').version") node $(node -v)"; } > results/versions.txt
