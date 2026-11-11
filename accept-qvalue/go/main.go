// munnerz/goautoneg (Kubernetes apimachinery), golang/gddo httputil.NegotiateContentType, elnormous/contenttype
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/elnormous/contenttype"
	"github.com/golang/gddo/httputil"
	"github.com/munnerz/goautoneg"
)

type Case struct {
	ID     string   `json:"id"`
	Accept *string  `json:"accept"`
	Offers []string `json:"offers"`
}
type Row struct {
	ID     string  `json:"id"`
	Choice *string `json:"choice"`
}

func str(s string) *string { return &s }

func guard(f func() *string) (r *string) {
	defer func() {
		if e := recover(); e != nil {
			r = str(fmt.Sprintf("ERR panic: %v", e))
		}
	}()
	return f()
}

func main() {
	var cases []Case
	if err := json.NewDecoder(os.Stdin).Decode(&cases); err != nil {
		panic(err)
	}
	out := map[string][]Row{}
	for _, c := range cases {
		req, _ := http.NewRequest("GET", "http://127.0.0.1/", nil)
		hdr := ""
		if c.Accept != nil {
			hdr = *c.Accept
			req.Header["Accept"] = []string{hdr}
		}
		out["goautoneg"] = append(out["goautoneg"], Row{c.ID, guard(func() *string {
			// absent header: callers pass r.Header.Get("Accept"), i.e. ""
			if r := goautoneg.Negotiate(hdr, c.Offers); r != "" {
				return str(r)
			}
			return nil
		})})
		out["gddo"] = append(out["gddo"], Row{c.ID, guard(func() *string {
			if r := httputil.NegotiateContentType(req, c.Offers, ""); r != "" {
				return str(r)
			}
			return nil
		})})
		out["contenttype"] = append(out["contenttype"], Row{c.ID, guard(func() *string {
			avail := []contenttype.MediaType{}
			for _, o := range c.Offers {
				avail = append(avail, contenttype.NewMediaType(o))
			}
			mt, _, err := contenttype.GetAcceptableMediaType(req, avail)
			if err != nil {
				return nil
			}
			return str(mt.String())
		})})
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", " ")
	enc.Encode(out)
}
