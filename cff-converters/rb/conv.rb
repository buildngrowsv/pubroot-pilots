# ruby-cff (the library behind GitHub's "Cite this repository"): usage conv.rb FILE bib|apa|validate
require "cff"
f, fmt = ARGV
if fmt == "validate"
  ok, errs = CFF::File.validate(f, fail_on_filename: false) rescue [false, [$!.message]]
  puts(ok ? "valid" : "invalid: #{Array(errs).map(&:to_s).join('; ')[0,300]}")
else
  c = CFF::Index.read(File.read(f))
  puts(fmt == "apa" ? c.to_apalike : c.to_bibtex)
end
