#!/usr/bin/python3
import os, sys, subprocess
_thisdir = os.path.split(os.path.abspath(__file__))[0]

ZIG = os.path.join(_thisdir, 'zig-linux-x86_64-0.13.0/zig')
C3 = '/usr/local/bin/c3c'
EMCC = 'emcc'

islinux=iswindows=isapple=c3gz=c3zip=None
if sys.platform == 'win32':
	c3zip = 'https://github.com/c3lang/c3c/releases/download/latest/c3-windows.zip'
	C3 = os.path.join(_thisdir,'c3/c3c.exe')
	iswindows=True
elif sys.platform == 'darwin':
	c3zip = 'https://github.com/c3lang/c3c/releases/download/latest/c3-macos.zip'
	isapple=True
else:
	c3gz = 'https://github.com/c3lang/c3c/releases/download/latest/c3-ubuntu-20.tar.gz'
	islinux=True

if not os.path.isfile(ZIG):
	if not os.path.isfile('zig-linux-x86_64-0.13.0.tar.xz'):
		cmd = 'wget -c https://ziglang.org/download/0.13.0/zig-linux-x86_64-0.13.0.tar.xz'
		print(cmd)
		subprocess.check_call(cmd.split())
	cmd = 'tar -xvf zig-linux-x86_64-0.13.0.tar.xz'
	print(cmd)
	subprocess.check_call(cmd.split())

ZIG_VER = subprocess.check_output([ZIG, 'version']).decode('utf-8')
print('zig version:', ZIG_VER)

if not os.path.isfile(C3):
	C3 = '/opt/c3/c3c'
	if not os.path.isfile(C3):
		if not os.path.isdir('./c3'):
			if c3gz:
				if not os.path.isfile('c3-ubuntu-20.tar.gz'):
					cmd = 'wget -c %s' % c3gz
					print(cmd)
					subprocess.check_call(cmd.split())
				cmd = 'tar -xvf c3-ubuntu-20.tar.gz'
				print(cmd)
				subprocess.check_call(cmd.split())
			elif c3zip and iswindows:
				if not os.path.isfile('c3-windows.zip'):
					cmd = ['C:/Windows/System32/curl.exe', '-o', 'c3-windows.zip', c3zip]
					print(cmd)
					subprocess.check_call(cmd)
			elif c3zip:
				if not os.path.isfile('c3-macos.zip'):
					cmd = ['curl', '-o', 'c3-macos.zip', c3zip]
					print(cmd)
					subprocess.check_call(cmd)

		if islinux:
			C3 = os.path.abspath('./c3/c3c')
		elif iswindows:
			C3 = os.path.abspath('./c3/c3c.exe')

assert os.path.isfile(C3)
print('c3c:', C3)


def zig_compile(zig, name='test-zig', freestanding=True):
	tmp = '/tmp/%s.zig' % name
	open(tmp,'w').write(zig)

	cmd = [ZIG, 'build-exe']
	target = 'wasm32-wasi'
	if freestanding:
		target = 'wasm32-freestanding-musl'

	cmd += [
		'-O', 'ReleaseSmall', '-target', target,  
		'-fno-entry',
		'--export-table', '-rdynamic',
		tmp
	]
	print(cmd)
	subprocess.check_call(cmd, cwd='/tmp')

	return '/tmp/%s.wasm' % name

def c3_compile(c3, name='test-c3'):
	tmp = '/tmp/%s.c3' % name
	open(tmp,'w').write(c3)
	cmd = [
		C3, '--target', 'wasm32', 'compile',
		'--output-dir', '/tmp',
		'--obj-out', '/tmp',
		'--build-dir', '/tmp',
		#'--print-output',
		'--link-libc=no', '--use-stdlib=no', '--no-entry', '--reloc=none', '-z', '--export-table',
		'-Oz',
		'-o', name,
		tmp
	]
	print(cmd)
	subprocess.check_call(cmd)
	return '/tmp/%s.wasm' % name

def c_compile(c, name='test-c'):
	tmp = '/tmp/%s.c' % name
	open(tmp,'w').write(c)
	output = '/tmp/%s.wasm32' % name
	cmd = [
		EMCC, '-o', output, 
		"-s","WASM=1",
		'-s', 'ERROR_ON_UNDEFINED_SYMBOLS=0',
		'-Oz',
		tmp
	]
	print(cmd)
	subprocess.check_call(cmd)



TESTS = {
	'helloworld':{
		'zig': '''
extern fn printn( ptr: [*]const u8, len:c_int) void;
export fn main() void {
	printn("hello world", 11);
}
		''',
		'c3':'''
extern fn void printn(char *ptr, int len);
fn void main(){
	printn("hello world", 11);
}
		''',
		'c':'''
extern void printn(char *ptr, int len);
void main(){
	printn("hello world", 11);
}
		''',
	}


}


def run_tests():
	for name in TESTS:
		print('test:', name)
		t = TESTS[name]
		if 'zig' in t:
			wasm = zig_compile(t['zig'])
			print(wasm)
		if 'c3' in t:
			wasm = c3_compile(t['c3'])
			print(wasm)
		if 'c' in t:
			wasm = c_compile(t['c'])
			print(wasm)


	os.system('ls -l /tmp/*.wasm')


if __name__=='__main__':
	run_tests()