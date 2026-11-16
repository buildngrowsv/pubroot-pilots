// Reads cases.json on stdin; writes {lib: {case: {ok, times|err}}} for three Go cron libraries.
// robfig/cron/v3: cron.ParseStandard(expr) then Schedule.Next (zero time = no further activation).
// adhocore/gronx: gronx.NextTickAfter(expr, t, false) (strictly after t), after gronx.New().IsValid(expr).
// hashicorp/cronexpr: cronexpr.Parse(expr) then Expression.Next (zero time = none).
// Each (library, case) runs in a goroutine with a 10 s limit (TIMEOUT otherwise).
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/adhocore/gronx"
	"github.com/hashicorp/cronexpr"
	"github.com/robfig/cron/v3"
)

type tcase struct {
	ID   string `json:"id"`
	Expr string `json:"expr"`
}
type input struct {
	Start string  `json:"start"`
	N     int     `json:"n"`
	Cases []tcase `json:"cases"`
}

func fmtT(t time.Time) string {
	t = t.UTC()
	s := t.Format("2006-01-02T15:04") + "Z"
	if t.Second() != 0 || t.Nanosecond() != 0 {
		s += fmt.Sprintf("+%ds", t.Second())
	}
	return s
}

func run(f func() (out []string, err error)) map[string]any {
	ch := make(chan map[string]any, 1)
	go func() {
		defer func() {
			if r := recover(); r != nil {
				ch <- map[string]any{"ok": false, "err": fmt.Sprintf("panic: %v", r)}
			}
		}()
		out, err := f()
		if err != nil {
			ch <- map[string]any{"ok": false, "err": trunc(err.Error())}
			return
		}
		if out == nil {
			out = []string{}
		}
		ch <- map[string]any{"ok": true, "times": out}
	}()
	select {
	case r := <-ch:
		return r
	case <-time.After(10 * time.Second):
		return map[string]any{"ok": false, "err": "TIMEOUT"}
	}
}

func trunc(s string) string {
	if len(s) > 70 {
		return s[:70]
	}
	return s
}

func main() {
	var in input
	if err := json.NewDecoder(os.Stdin).Decode(&in); err != nil {
		panic(err)
	}
	start, _ := time.Parse(time.RFC3339, in.Start)
	res := map[string]map[string]any{"robfig-cron": {}, "gronx": {}, "cronexpr": {}}
	for _, c := range in.Cases {
		e := c.Expr
		res["robfig-cron"][c.ID] = run(func() ([]string, error) {
			s, err := cron.ParseStandard(e)
			if err != nil {
				return nil, err
			}
			out := []string{}
			t := start
			for i := 0; i < in.N; i++ {
				t = s.Next(t)
				if t.IsZero() {
					break
				}
				out = append(out, fmtT(t))
			}
			return out, nil
		})
		res["gronx"][c.ID] = run(func() ([]string, error) {
			if !gronx.New().IsValid(e) {
				return nil, fmt.Errorf("IsValid=false")
			}
			out := []string{}
			t := start
			for i := 0; i < in.N; i++ {
				n, err := gronx.NextTickAfter(e, t, false)
				if err != nil {
					if len(out) > 0 {
						break
					}
					return nil, err
				}
				out = append(out, fmtT(n))
				t = n
			}
			return out, nil
		})
		res["cronexpr"][c.ID] = run(func() ([]string, error) {
			x, err := cronexpr.Parse(e)
			if err != nil {
				return nil, err
			}
			out := []string{}
			t := start
			for i := 0; i < in.N; i++ {
				t = x.Next(t)
				if t.IsZero() {
					break
				}
				out = append(out, fmtT(t))
			}
			return out, nil
		})
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", " ")
	enc.Encode(res)
}
