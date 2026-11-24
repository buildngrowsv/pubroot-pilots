// Go: the reference (distribution/reference ParseNormalizedNamed + TagNameOnly) and go-containerregistry
// name.ParseReference with default options. Usage: go-refs CASES.json
// Output: {lib: {id: {"ref": [registry, repository, tag|null, digest|null]} | {"error": "..."}}}
package main

import (
	"encoding/json"
	"os"

	"github.com/distribution/reference"
	"github.com/google/go-containerregistry/pkg/name"
)

type res map[string]any

func sp(s string) *string { return &s }

func dist(s string) res {
	n, err := reference.ParseNormalizedNamed(s)
	if err != nil {
		return res{"error": err.Error()}
	}
	n = reference.TagNameOnly(n)
	var tag, dg *string
	if t, ok := n.(reference.Tagged); ok {
		tag = sp(t.Tag())
	}
	if d, ok := n.(reference.Digested); ok {
		dg = sp(d.Digest().String())
	}
	return res{"ref": []*string{sp(reference.Domain(n)), sp(reference.Path(n)), tag, dg}}
}

func ggcr(s string) res {
	r, err := name.ParseReference(s)
	if err != nil {
		return res{"error": err.Error()}
	}
	c := r.Context()
	var tag, dg *string
	switch v := r.(type) {
	case name.Tag:
		tag = sp(v.TagStr())
	case name.Digest:
		dg = sp(v.DigestStr())
	}
	return res{"ref": []*string{sp(c.RegistryStr()), sp(c.RepositoryStr()), tag, dg}}
}

func main() {
	var cases []struct {
		ID string `json:"id"`
		S  string `json:"s"`
	}
	b, _ := os.ReadFile(os.Args[1])
	if err := json.Unmarshal(b, &cases); err != nil {
		panic(err)
	}
	out := map[string]map[string]res{"distribution/reference": {}, "go-containerregistry": {}}
	for _, c := range cases {
		out["distribution/reference"][c.ID] = dist(c.S)
		out["go-containerregistry"][c.ID] = ggcr(c.S)
	}
	e := json.NewEncoder(os.Stdout)
	e.SetEscapeHTML(false)
	e.SetIndent("", " ")
	e.Encode(out)
}
