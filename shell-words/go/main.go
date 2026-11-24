// Split and quote runners for Go libraries. Usage: go-words split|quote CASES.json > out.json
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	gshlex "github.com/google/shlex"
	shellquote "github.com/kballard/go-shellquote"
	shellwords "github.com/mattn/go-shellwords"
	"mvdan.cc/sh/v3/shell"
	"mvdan.cc/sh/v3/syntax"
)

type res struct {
	Argv  any    `json:"argv,omitempty"`
	Error string `json:"error,omitempty"`
}

func trunc(s string) string {
	if len(s) > 120 {
		return s[:120]
	}
	return s
}

func wrapList(f func(string) ([]string, error)) func(string) res {
	return func(s string) (r res) {
		defer func() {
			if p := recover(); p != nil {
				r = res{Error: trunc(fmt.Sprint("panic: ", p))}
			}
		}()
		v, err := f(s)
		if err != nil {
			return res{Error: trunc(err.Error())}
		}
		if v == nil {
			v = []string{}
		}
		return res{Argv: v}
	}
}

func wrapStr(f func(string) (string, error)) func(string) res {
	return func(s string) res {
		v, err := f(s)
		if err != nil {
			return res{Error: trunc(err.Error())}
		}
		return res{Argv: v}
	}
}

func main() {
	mode, file := os.Args[1], os.Args[2]
	b, _ := os.ReadFile(file)
	var cases []struct{ ID, S string }
	json.Unmarshal(b, &cases)
	// same environment as the sh reference (oracle.py): only PATH and HOME are set
	empty := func(k string) string {
		switch k {
		case "HOME":
			return "/nonexistent-home"
		case "PATH":
			return "/nonexistent"
		}
		return ""
	}
	var T map[string]func(string) res
	if mode == "split" {
		T = map[string]func(string) res{
			"google/shlex":    wrapList(gshlex.Split),
			"go-shellwords":   wrapList(shellwords.Parse),
			"go-shellquote":   wrapList(shellquote.Split),
			"mvdan sh Fields": wrapList(func(s string) ([]string, error) { return shell.Fields(s, empty) }),
		}
	} else {
		T = map[string]func(string) res{
			"go-shellquote": wrapStr(func(s string) (string, error) { return shellquote.Join(s), nil }),
			"mvdan sh Quote": wrapStr(func(s string) (string, error) { return syntax.Quote(s, syntax.LangPOSIX) }),
		}
	}
	out := map[string]map[string]res{}
	for n, f := range T {
		out[n] = map[string]res{}
		for _, c := range cases {
			out[n][c.ID] = f(c.S)
		}
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", " ")
	enc.Encode(out)
	_ = strings.TrimSpace
}
