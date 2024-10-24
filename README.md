# hello world test

* zig version: 0.13.0
* c3 version: 0.6.3 (LLVM 17.0.6)
* emcc version: 3.1.6

* zig wasm: 152 bytes
* c3 wasm: 143 bytes
* emcc wasm: 142 bytes

## zig
```zig
extern fn printn( ptr: [*]const u8, len:c_int) void;
export fn main() void {
	printn("hello world", 11);
}
```

## c3
```c3
extern fn void printn(char *ptr, int len);
fn void main(){
	printn("hello world", 11);
}
```

## c
```c
extern void printn(char *ptr, int len);
void main(){
	printn("hello world", 11);
}
```
