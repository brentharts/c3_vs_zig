# hello world test

* zig version: 0.13.0
...wasm = 152 bytes
...wasm-opt -Oz = 135 bytes
* c3 version: 0.6.3 (LLVM 17.0.6)
...wasm = 251 bytes
...wasm-opt -Oz = 177 bytes

## zig
```zig
extern fn printn(
	ptr: [*]const u8, 
	len:c_int
	) void;

export fn main() void {
	printn("hello world", 11);
}
```

## c3
```c
extern fn void printn(
	char *ptr, 
	int len
	);

fn void main() 
	@extern("main") 
	@wasm {
	printn("hello world", 11);
}
```

