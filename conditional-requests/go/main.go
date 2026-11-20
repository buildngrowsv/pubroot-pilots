// Go net/http: mode "servecontent" sets a strong ETag ("<size>-<unix mtime hex>") and calls http.ServeContent, the
// documented way to get ETag preconditions; mode "fileserver" is a plain http.FileServer (no ETag). 127.0.0.1:PORT
package main

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
)

func main() {
	wd, _ := os.Getwd()
	data := filepath.Join(wd, "data")
	mode, port := os.Args[1], os.Args[2]
	var h http.Handler
	if mode == "fileserver" {
		h = http.FileServer(http.Dir(data))
	} else {
		h = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			f, err := os.Open(filepath.Join(data, filepath.Base(r.URL.Path)))
			if err != nil {
				http.NotFound(w, r)
				return
			}
			defer f.Close()
			st, _ := f.Stat()
			w.Header().Set("ETag", fmt.Sprintf("\"%x-%x\"", st.Size(), st.ModTime().Unix()))
			http.ServeContent(w, r, st.Name(), st.ModTime(), f)
		})
	}
	http.ListenAndServe("127.0.0.1:"+port, h)
}
