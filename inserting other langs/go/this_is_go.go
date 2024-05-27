package main

// https://ru.stackoverflow.com/questions/1421679/python-go-%D1%87%D0%B5%D1%80%D0%B5%D0%B7-c
import (
	"C"
	"fmt"
)

//export hello_go
func hello_go() {
	fmt.Println("This is go code!")
}

func main() {}
