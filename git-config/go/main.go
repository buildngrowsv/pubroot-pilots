// Go subject: go-git v5 plumbing/format/config Decoder. Usage: go-gitconfig CASES.json
// Output: {"go-git": {id: {"entries": [[key, value|null]...]} | {"error": "..."}}}. Keys as in py/run.py.
package main

import (
	"bytes"
	"encoding/json"
	"os"
	"strings"

	"github.com/go-git/go-git/v5/plumbing/format/config"
)

type res struct {
	Entries *[][2]*string `json:"entries,omitempty"`
	Error   string        `json:"error,omitempty"`
}

func key(sec string, sub *string, name string) string {
	k := strings.ToLower(sec)
	if sub != nil {
		k += "." + *sub
	}
	return k + "." + strings.ToLower(name)
}

func parse(text string) (r res) {
	defer func() {
		if p := recover(); p != nil {
			r = res{Error: "panic"}
		}
	}()
	c := config.New()
	if err := config.NewDecoder(bytes.NewBufferString(text)).Decode(c); err != nil {
		return res{Error: err.Error()}
	}
	ents := [][2]*string{}
	add := func(k string, v string) { kk, vv := k, v; ents = append(ents, [2]*string{&kk, &vv}) }
	for _, s := range c.Sections {
		for _, o := range s.Options {
			add(key(s.Name, nil, o.Key), o.Value)
		}
		for _, ss := range s.Subsections {
			n := ss.Name
			for _, o := range ss.Options {
				add(key(s.Name, &n, o.Key), o.Value)
			}
		}
	}
	return res{Entries: &ents}
}

func main() {
	var cases []struct {
		ID   string `json:"id"`
		Text string `json:"text"`
	}
	b, _ := os.ReadFile(os.Args[1])
	if err := json.Unmarshal(b, &cases); err != nil {
		panic(err)
	}
	out := map[string]res{}
	for _, c := range cases {
		out[c.ID] = parse(c.Text)
	}
	e := json.NewEncoder(os.Stdout)
	e.SetEscapeHTML(false)
	e.SetIndent("", " ")
	e.Encode(map[string]map[string]res{"go-git": out})
}
