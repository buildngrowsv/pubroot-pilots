// Go net/http http.ServeContent (the logic behind http.FileServer / http.ServeFile) on 127.0.0.1:PORT
package main

import (
	"net/http"
	"os"
	"path/filepath"
)

func main() {
	exe, _ := os.Getwd()
	data := filepath.Join(exe, "data")
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		f, err := os.Open(filepath.Join(data, filepath.Base(r.URL.Path)))
		if err != nil {
			http.NotFound(w, r)
			return
		}
		defer f.Close()
		st, _ := f.Stat()
		http.ServeContent(w, r, st.Name(), st.ModTime(), f)
	})
	http.ListenAndServe("127.0.0.1:"+os.Args[1], nil)
}
