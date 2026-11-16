// Reads cases.json on stdin; writes {"go-spdx": {case: {ok, canon, leaves, probes}|{ok:false, err}}}
// using only the public API of github.com/github/go-spdx/v2/spdxexp (no access to its parse tree).
package main

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/github/go-spdx/v2/spdxexp"
	"github.com/github/go-spdx/v2/spdxexp/spdxlicenses"
)

type probe struct {
	Allow []string `json:"allow"`
	Sat   bool     `json:"sat"`
}
type tcase struct {
	ID     string  `json:"id"`
	Expr   string  `json:"expr"`
	Probes []probe `json:"probes"`
}

func main() {
	var cases []tcase
	if err := json.NewDecoder(os.Stdin).Decode(&cases); err != nil {
		panic(err)
	}
	res := map[string]any{}
	for _, c := range cases {
		r := map[string]any{}
		norm, invalid := spdxexp.ValidateAndNormalizeLicensesWithOptions([]string{c.Expr}, spdxexp.ValidateLicensesOptions{})
		r["ok"] = len(invalid) == 0
		if len(invalid) == 0 && len(norm) == 1 {
			r["canon"] = norm[0]
		}
		if leaves, err := spdxexp.ExtractLicenses(c.Expr); err == nil {
			sort.Strings(leaves)
			r["leaves"] = leaves
		} else {
			r["extract_err"] = err.Error()
		}
		if len(c.Probes) > 0 {
			ps := []any{}
			for _, p := range c.Probes {
				ok, err := spdxexp.Satisfies(c.Expr, p.Allow)
				if err != nil {
					ps = append(ps, "ERR")
				} else {
					ps = append(ps, ok)
				}
			}
			r["probes"] = ps
		}
		res[c.ID] = r
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", " ")
	enc.SetEscapeHTML(false)
	enc.Encode(map[string]any{"go-spdx": res, "_list_version": spdxlicenses.LicenseListVersion()})
}
