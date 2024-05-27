package main

import ("C"
        "strings"
)

//export Echo
func Echo(s *C.char) *C.char {
    return C.CString(
      strings.ToUpper(
        C.GoString(s)))
}

func main() {}