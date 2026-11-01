package main

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"strconv"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "one integer between 1 and 1000000 is required")
		os.Exit(2)
	}
	value, err := strconv.ParseInt(os.Args[1], 10, 64)
	if err != nil || value < 1 || value > 1000000 {
		fmt.Fprintln(os.Stderr, "invalid integer")
		os.Exit(2)
	}
	if err := json.NewEncoder(os.Stdout).Encode(map[string]any{
		"architecture": runtime.GOARCH,
		"input":        value,
		"square":       value * value,
	}); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
