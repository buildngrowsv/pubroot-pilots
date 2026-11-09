package main

import (
  "encoding/json"
  "fmt"
  "os"
  "path/filepath"
  "strings"

  "github.com/moby/patternmatcher"
  "github.com/moby/patternmatcher/ignorefile"
)

func main() {
  if len(os.Args) < 3 {
    fmt.Fprintln(os.Stderr, "usage: main ignorefile meta.json")
    os.Exit(2)
  }
  data, err := os.ReadFile(os.Args[1])
  if err != nil { panic(err) }
  patterns, err := ignorefile.ReadAll(strings.NewReader(string(data)))
  if err != nil {
    enc, _ := json.Marshal(map[string]any{"error": err.Error()})
    fmt.Println(string(enc)); return
  }
  pm, err := patternmatcher.New(patterns)
  if err != nil {
    enc, _ := json.Marshal(map[string]any{"error": err.Error()})
    fmt.Println(string(enc)); return
  }
  var meta struct {
    Paths [][]any `json:"paths"`
  }
  b, err := os.ReadFile(os.Args[2])
  if err != nil { panic(err) }
  if err := json.Unmarshal(b, &meta); err != nil { panic(err) }
  out := map[string]bool{}
  for _, pair := range meta.Paths {
    p := pair[0].(string)
    m, err := pm.MatchesOrParentMatches(filepath.ToSlash(p))
    if err != nil { panic(err) }
    out[p] = m
  }
  enc, _ := json.Marshal(out)
  fmt.Println(string(enc))
}
